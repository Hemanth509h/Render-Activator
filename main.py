from flask import Flask, render_template_string, request, redirect, url_for
import threading
import time
import requests
import os

app = Flask(__name__)

# In-memory storage for URLs and settings
urls = []
ping_interval = 14 # Default minutes
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
        .container { max-width: 600px; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .status-badge { font-size: 0.8em; }
    </style>
</head>
<body>
    <div class="container mt-5">
        <h2 class="mb-4">Render Pinger Control</h2>
        
        <form action="/settings" method="post" class="mb-4">
            <label class="form-label">Ping Interval (minutes):</label>
            <div class="input-group">
                <input type="number" name="interval" class="form-control" value="{{ interval }}" min="1" max="60" required>
                <button class="btn btn-secondary" type="submit">Update Interval</button>
            </div>
        </form>

        <form action="/add" method="post" class="mb-4">
            <div class="input-group">
                <input type="url" name="url" class="form-control" placeholder="https://your-app.onrender.com" required>
                <button class="btn btn-primary" type="submit">Add URL</button>
            </div>
        </form>

        <ul class="list-group">
            {% for url in urls %}
            <li class="list-group-item d-flex justify-content-between align-items-center">
                {{ url }}
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
        
        <div class="mt-4 text-muted small">
            Currently pinging every {{ interval }} minutes to prevent Render sleep.
        </div>
    </div>
</body>
</html>
"""

# ... (existing code above index function)

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, urls=urls, interval=ping_interval)

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
        for url in current_urls:
            try:
                print(f"Pinging {url}...")
                response = requests.get(url, timeout=10)
                print(f"Response from {url}: {response.status_code}")
            except Exception as e:
                print(f"Error pinging {url}: {e}")
        
        # Sleep for the configured interval
        time.sleep(ping_interval * 60)

if __name__ == "__main__":
    t = threading.Thread(target=pinger_thread, daemon=True)
    t.start()
    app.run(host='0.0.0.0', port=5000)
