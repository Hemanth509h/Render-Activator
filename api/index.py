from flask import Flask, render_template_string, request, redirect, url_for
import requests
import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# In-memory storage (Note: Vercel is serverless, memory is not persistent)
urls = []
ping_interval = 1
ping_logs = []

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Render Pinger (Vercel Mode)</title>
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
        <h2 class="mb-4">Render Pinger <span class="badge bg-warning text-dark">Vercel Serverless</span></h2>
        
        <div class="alert alert-info">
            <strong>Note:</strong> Vercel is serverless. Background threads do not persist. 
            This interface is for configuration only. For actual pinging, use a Cron Job.
        </div>

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
                        </ul>
                    </div>
                </div>
            </div>
            
            <div class="col-lg-9">
                <div class="log-container" id="log-container">
                    <div class="text-muted italic">Logs are not persistent in Serverless mode.</div>
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

# Vercel expectations: app or application
application = app
