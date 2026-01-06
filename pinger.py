import time
import requests
import sys

# Default URL list - users can add their URLs here
URLS = [
     "https://canteen-f0rq.onrender.com",
]

# You can also pass URLs as command line arguments
# Example: python pinger.py https://site1.com https://site2.com
if len(sys.argv) > 1:
    URLS.extend(sys.argv[1:])

# Render spins down free tier apps after 15 minutes of inactivity.
# We ping every 14 minutes to keep it active.
INTERVAL = 14 * 60  # 14 minutes in seconds

def ping_urls():
    if not URLS:
        print("No URLs configured.")
        print("Please edit 'pinger.py' to add URLs or pass them as arguments.")
        print("Usage: python pinger.py <url1> <url2> ...")
        return

    print(f"Starting pinger for {len(URLS)} URLs. Interval: {INTERVAL} seconds.")
    
    while True:
        for url in URLS:
            try:
                print(f"[{time.strftime('%H:%M:%S')}] Pinging {url}...")
                response = requests.get(url, timeout=10)
                print(f"  Status: {response.status_code}")
            except Exception as e:
                print(f"  Failed: {str(e)}")
        
        print(f"Sleeping for {INTERVAL} seconds...")
        time.sleep(INTERVAL)

if __name__ == "__main__":
    ping_urls()
