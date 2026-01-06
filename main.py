import os
import datetime
import logging
import threading
import time
import requests
import urllib3
from flask import Flask, render_template_string, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

# Database Setup
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class TargetURL(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), unique=True, nullable=False)

# Suppress insecure request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# App Initialization
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "a-very-secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
db.init_app(app)

# In-memory pinger status
ping_interval = 1 
ping_logs = []
MAX_LOGS = 100
pinger_active = True

def pinger_thread():
    logger.info("Background pinger thread started.")
    time.sleep(5)
    while pinger_active:
        with app.app_context():
            current_urls = [t.url for t in TargetURL.query.all()]
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if not current_urls:
            log_msg = f"[{timestamp}] Waiting for URLs to ping..."
            if not ping_logs or "Waiting" not in ping_logs[-1]:
                ping_logs.append(log_msg)
        else:
            for url in current_urls:
                try:
                    log_msg = f"[{timestamp}] Pinging {url}..."
                    ping_logs.append(log_msg)
                    
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.5',
                        'Connection': 'keep-alive',
                    }
                    
                    response = requests.get(url, timeout=20, verify=False, headers=headers)
                    res_msg = f"[{timestamp}] Response from {url}: {response.status_code}"
                    ping_logs.append(res_msg)
                except Exception as e:
                    err_msg = f"[{timestamp}] Error pinging {url}: {str(e)[:200]}"
                    ping_logs.append(err_msg)
        
        while len(ping_logs) > MAX_LOGS:
            ping_logs.pop(0)
        time.sleep(ping_interval * 60)

with app.app_context():
    db.create_all()

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
                    <p>Logs auto-refreshing every 5s</p>
                </div>
            </div>
            
            <div class="col-lg-9">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <h5 class="mb-0">System Activity Logs</h5>
                    <span class="badge bg-dark">{{ logs|length }} entries</span>
                </div>
                <div class="log-container" id="log-container">
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

    <script>
        function refreshLogs() {
            fetch('/')
                .then(response => response.text())
                .then(html => {
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(html, 'text/html');
                    const newLogs = doc.getElementById('log-container').innerHTML;
                    const logContainer = document.getElementById('log-container');
                    if (logContainer.innerHTML !== newLogs) {
                        logContainer.innerHTML = newLogs;
                    }
                })
                .catch(err => console.error('Error refreshing logs:', err));
        }
        setInterval(refreshLogs, 5000);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    urls = [t.url for t in TargetURL.query.all()]
    return render_template_string(HTML_TEMPLATE, urls=urls, interval=ping_interval, logs=list(reversed(ping_logs)))

@app.route('/settings', methods=['POST'])
def update_settings():
    global ping_interval
    try:
        new_interval = int(request.form.get('interval', 1))
        if 1 <= new_interval <= 1440:
            ping_interval = new_interval
    except ValueError:
        pass
    return redirect(url_for('index'))

@app.route('/add', methods=['POST'])
def add_url():
    url = request.form.get('url')
    if url:
        existing = TargetURL.query.filter_by(url=url).first()
        if not existing:
            new_target = TargetURL(url=url)
            db.session.add(new_target)
            db.session.commit()
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ping_logs.append(f"[{timestamp}] URL added: {url}")
    return redirect(url_for('index'))

@app.route('/remove', methods=['POST'])
def remove_url():
    url = request.form.get('url')
    target = TargetURL.query.filter_by(url=url).first()
    if target:
        db.session.delete(target)
        db.session.commit()
    return redirect(url_for('index'))

# Export for both local and serverless
application = app
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
