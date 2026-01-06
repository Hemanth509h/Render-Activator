from flask import Flask, render_template_string, request, redirect, url_for
import threading
import time
import requests
import os
import datetime

app = Flask(__name__)

# In-memory storage for URLs, settings, and logs
urls = []
ping_interval = 14 # Default minutes
ping_logs = []
MAX_LOGS = 50
# Global variable to control the pinger thread
pinger_active = True

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Render Pinger</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { padding: 20px; background-color: #f8f9fa; }
        .container { max-width: 800px; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .log-container { max-height: 300px; overflow-y: auto; background: #212529; color: #0f0; padding: 15px; border-radius: 5px; font-family: monospace; font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="container mt-5">
        <h2 class="mb-4">Render Pinger Control</h2>
        
        <div class="row">
            <div class="col-md-6">
                <form action="/settings" method="post" class="mb-4">
                    <label class="form-label">Ping Interval (minutes):</label>
                    <div class="input-group">
                        <input type="number" name="interval" class="form-control" value="{{ interval }}" min="1" max="60" required>
                        <button class="btn btn-secondary" type="submit">Update</button>
                    </div>
                </form>

                <form action="/add" method="post" class="mb-4">
                    <label class="form-label">Add New URL:</label>
                    <div class="input-group">
                        <input type="url" name="url" class="form-control" placeholder="https://your-app.onrender.com" required>
                        <button class="btn btn-primary" type="submit">Add URL</button>
                    </div>
                </form>

                <ul class="list-group mb-4">
                    {% for url in urls %}
                    <li class="list-group-item d-flex justify-content-between align-items-center">
                        <span class="text-truncate" style="max-width: 250px;">{{ url }}</span>
                        <form action="/remove" method="post" style="margin: 0;">
                            <input type="hidden" name="url" value="{{ url }}">
                            <button type="submit" class="btn btn-danger btn-sm">Remove</button>
                        </form>
                    </li>
                    {% endfor %}
                    {% if not urls %}
                    <li class="list-group-item text-muted">No URLs being pinged.</li>
                    {% endif %}
                </ul>
            </div>
            
            <div class="col-md-6">
                <label class="form-label">Recent Activity:</label>
                <div class="log-container">
                    {% for log in logs %}
                    <div>{{ log }}</div>
                    {% endfor %}
                    {% if not logs %}
                    <div class="text-muted small">Waiting for activity...</div>
                    {% endif %}
                </div>
                <div class="mt-2 text-muted small">
                    Showing last {{ max_logs }} events.
                </div>
            </div>
        </div>
        
        <div class="mt-4 text-muted small border-top pt-3">
            Currently pinging every {{ interval }} minutes to prevent Render sleep.
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, urls=urls, interval=ping_interval, logs=list(reversed(ping_logs)), max_logs=MAX_LOGS)

# (new note for Vercel)
# Vercel is serverless, so background threads like pinger_thread 
# won't stay alive between requests. This app is best used 
# in a persistent environment like Replit.

@app.route('/settings', methods=['POST'])
def update_settings():
    global ping_interval
    try:
        new_interval = int(request.form.get('interval', 14))
        if 1 <= new_interval <= 1440: # Max 24 hours
            ping_interval = new_interval
    except ValueError:
        pass
    return redirect(url_for('index'))

@app.route('/add', methods=['POST'])
def add_url():
    url = request.form.get('url')
    if url and url not in urls:
        urls.append(url)
    return redirect(url_for('index'))

@app.route('/remove', methods=['POST'])
def remove_url():
    url = request.form.get('url')
    if url in urls:
        urls.remove(url)
    return redirect(url_for('index'))

def pinger_thread():
    print("Background pinger started.")
    while pinger_active:
        current_urls = list(urls) # Copy to avoid modification during iteration
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if not current_urls:
            log_msg = f"[{timestamp}] No URLs to ping."
            print(log_msg)
            ping_logs.append(log_msg)
        else:
            for url in current_urls:
                try:
                    log_msg = f"[{timestamp}] Pinging {url}..."
                    print(log_msg)
                    ping_logs.append(log_msg)
                    
                    response = requests.get(url, timeout=10)
                    
                    res_msg = f"[{timestamp}] Response from {url}: {response.status_code}"
                    print(res_msg)
                    ping_logs.append(res_msg)
                except Exception as e:
                    err_msg = f"[{timestamp}] Error pinging {url}: {e}"
                    print(err_msg)
                    ping_logs.append(err_msg)
        
        # Keep logs within limit
        while len(ping_logs) > MAX_LOGS:
            ping_logs.pop(0)
            
        # Sleep for the configured interval
        time.sleep(ping_interval * 60)

if __name__ == "__main__":
    t = threading.Thread(target=pinger_thread, daemon=True)
    t.start()
    app.run(host='0.0.0.0', port=5000)
