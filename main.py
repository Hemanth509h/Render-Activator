from flask import Flask, render_template_string, request, redirect, url_for
import threading
import time
import requests
import os
import datetime
import logging

# Configure logging to see activity in the console
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# In-memory storage for URLs, settings, and logs
# Global variables need careful handling with Gunicorn
urls = []
ping_interval = 1 # Changed default to 1 min for faster feedback
ping_logs = []
MAX_LOGS = 100
pinger_active = True

def pinger_thread():
    logger.info("Background pinger thread started.")
    # Wait a bit for the app to settle
    time.sleep(2)
    while pinger_active:
        current_urls = list(urls)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if not current_urls:
            log_msg = f"[{timestamp}] Waiting for URLs to ping... (Current Interval: {ping_interval} min)"
            logger.debug(log_msg)
            # Avoid flooding logs if no URLs
            if not ping_logs or "Waiting" not in ping_logs[-1]:
                ping_logs.append(log_msg)
        else:
            for url in current_urls:
                try:
                    log_msg = f"[{timestamp}] Pinging {url}..."
                    logger.info(log_msg)
                    ping_logs.append(log_msg)
                    
                    response = requests.get(url, timeout=10)
                    
                    res_msg = f"[{timestamp}] Response from {url}: {response.status_code}"
                    logger.info(res_msg)
                    ping_logs.append(res_msg)
                except Exception as e:
                    err_msg = f"[{timestamp}] Error pinging {url}: {e}"
                    logger.error(err_msg)
                    ping_logs.append(err_msg)
        
        # Keep logs within limit
        while len(ping_logs) > MAX_LOGS:
            ping_logs.pop(0)
            
        # Sleep for the configured interval
        logger.debug(f"Pinger sleeping for {ping_interval} minute(s).")
        time.sleep(ping_interval * 60)

# Initialize app first
app = Flask(__name__)

# Start pinger thread
t = threading.Thread(target=pinger_thread, daemon=True)
t.start()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Render Pinger</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { padding: 20px; background-color: #f8f9fa; }
        .container-fluid { max-width: 1400px; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .log-container { height: 70vh; overflow-y: auto; background: #212529; color: #0f0; padding: 20px; border-radius: 5px; font-family: monospace; font-size: 1.1em; line-height: 1.5; }
    </style>
</head>
<body>
    <div class="container-fluid mt-3">
        <h2 class="mb-4">Render Pinger Control Center</h2>
        
        <div class="row">
            <div class="col-lg-3">
                <div class="card mb-4 shadow-sm">
                    <div class="card-body">
                        <h5 class="card-title">Settings</h5>
                        <form action="/settings" method="post" class="mb-3">
                            <label class="form-label small">Ping Interval (minutes):</label>
                            <div class="input-group input-group-sm">
                                <input type="number" name="interval" class="form-control" value="{{ interval }}" min="1" max="1440" required>
                                <button class="btn btn-secondary" type="submit">Update</button>
                            </div>
                        </form>

                        <form action="/add" method="post" class="mb-3">
                            <label class="form-label small">Add New URL:</label>
                            <div class="input-group input-group-sm">
                                <input type="url" name="url" class="form-control" placeholder="https://example.com" required>
                                <button class="btn btn-primary" type="submit">Add URL</button>
                            </div>
                        </form>
                    </div>
                </div>

                <div class="card shadow-sm">
                    <div class="card-body">
                        <h5 class="card-title">Active URLs</h5>
                        <ul class="list-group list-group-flush">
                            {% for url in urls %}
                            <li class="list-group-item d-flex justify-content-between align-items-center px-0">
                                <span class="text-truncate" style="max-width: 180px;" title="{{ url }}">{{ url }}</span>
                                <form action="/remove" method="post" style="margin: 0;">
                                    <input type="hidden" name="url" value="{{ url }}">
                                    <button type="submit" class="btn btn-outline-danger btn-sm border-0">×</button>
                                </form>
                            </li>
                            {% endfor %}
                            {% if not urls %}
                            <li class="list-group-item text-muted small px-0">No URLs added.</li>
                            {% endif %}
                        </ul>
                    </div>
                </div>
                
                <div class="mt-4 text-muted small border-top pt-3 text-center">
                    <p>Auto-refreshing every 10s</p>
                    <script>setTimeout(() => location.reload(), 10000);</script>
                </div>
            </div>
            
            <div class="col-lg-9">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <h5 class="mb-0">System Activity Logs</h5>
                    <span class="badge bg-dark">{{ logs|length }} entries</span>
                </div>
                <div class="log-container">
                    {% for log in logs %}
                    <div class="mb-1">
                        <span class="text-muted">{{ log[:21] }}</span>
                        <span>{{ log[21:] }}</span>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, urls=urls, interval=ping_interval, logs=list(reversed(ping_logs)))

@app.route('/settings', methods=['POST'])
def update_settings():
    global ping_interval
    try:
        new_interval = int(request.form.get('interval', 1))
        if 1 <= new_interval <= 1440:
            ping_interval = new_interval
            logger.info(f"Interval updated to {ping_interval} minutes")
    except ValueError:
        pass
    return redirect(url_for('index'))

@app.route('/add', methods=['POST'])
def add_url():
    url = request.form.get('url')
    if url and url not in urls:
        urls.append(url)
        logger.info(f"Added URL: {url}")
        # Trigger an immediate ping update log
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ping_logs.append(f"[{timestamp}] URL added, will ping in next cycle.")
    return redirect(url_for('index'))

@app.route('/remove', methods=['POST'])
def remove_url():
    url = request.form.get('url')
    if url in urls:
        urls.remove(url)
        logger.info(f"Removed URL: {url}")
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
