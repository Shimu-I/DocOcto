"""Downloads the page-view libraries (free, MIT/Apache) so the app works offline. Safe to re-run."""
import os, urllib.request
V = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "public", "vendor")
FILES = {"mammoth.js": "https://cdn.jsdelivr.net/npm/mammoth@1.6.0/mammoth.browser.min.js",
         "pdf.min.js": "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js",
         "pdf.worker.min.js": "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js"}
os.makedirs(V, exist_ok=True)
for name, url in FILES.items():
    path = os.path.join(V, name)
    if os.path.exists(path) and os.path.getsize(path) > 10000: continue
    try: urllib.request.urlretrieve(url, path); print("downloaded", name)
    except Exception as e: print("could not download", name, "- the page will load it from the CDN instead:", e)
