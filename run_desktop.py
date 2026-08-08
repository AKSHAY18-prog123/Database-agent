import os
import sys
import io
import webbrowser
import threading
import time
import uvicorn
from fastapi.staticfiles import StaticFiles

# Fix Windows GUI windowed mode stdout/stderr streams for Uvicorn logger
if sys.stdout is None:
    sys.stdout = io.StringIO()
if sys.stderr is None:
    sys.stderr = io.StringIO()

# Import FastAPI app from backend main
from backend.main import app

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and PyInstaller bundle."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# Mount bundled frontend static files if present
frontend_dist = get_resource_path(os.path.join("frontend", "dist"))
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")

def open_browser():
    time.sleep(1.5)
    webbrowser.open("http://127.0.0.1:8000")

if __name__ == "__main__":
    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run(app, host="127.0.0.1", port=8000, log_config=None)
