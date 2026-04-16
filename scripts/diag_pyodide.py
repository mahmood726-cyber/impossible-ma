"""Diagnose Pyodide cold load on headless Chrome.

Polls window.{PYODIDE_READY, PYODIDE_LOAD_ERROR} and the splash-status text every
5 seconds. Captures browser console on exit. Writes a timeline so we can see
WHICH stage stalls (CDN pyodide, 40 MB packages, micropip, wheel install).
"""

import http.server
import os
import socketserver
import sys
import threading
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

ROOT = Path(__file__).resolve().parents[1]
PORT = 8766
URL = f"http://localhost:{PORT}/impossible-ma.html"
WALL_SECS = int(sys.argv[1]) if len(sys.argv) > 1 else 420


def serve():
    os.chdir(ROOT)
    httpd = socketserver.TCPServer(("", PORT), http.server.SimpleHTTPRequestHandler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd


def main():
    httpd = serve()
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--window-size=1400,900")
    opts.set_capability("goog:loggingPrefs", {"browser": "ALL"})
    drv = webdriver.Chrome(options=opts)
    start = time.time()
    try:
        drv.get(URL)
        deadline = start + WALL_SECS
        last_status = None
        while time.time() < deadline:
            elapsed = int(time.time() - start)
            state = drv.execute_script(
                "return {ready: window.PYODIDE_READY === true, "
                "err: window.PYODIDE_LOAD_ERROR || null, "
                "status: (document.getElementById('splash-status')||{}).textContent || null};"
            )
            if state["status"] != last_status:
                print(f"[{elapsed:4d}s] splash: {state['status']!r}", flush=True)
                last_status = state["status"]
            if state["ready"]:
                print(f"[{elapsed:4d}s] PYODIDE_READY=true", flush=True)
                return 0
            if state["err"]:
                print(f"[{elapsed:4d}s] PYODIDE_LOAD_ERROR: {state['err']}", flush=True)
                return 2
            time.sleep(5)
        print(f"[{WALL_SECS}s] TIMEOUT — neither READY nor ERROR fired", flush=True)
        return 1
    finally:
        try:
            logs = drv.get_log("browser")
            print("\n--- console ---", flush=True)
            for entry in logs:
                print(f"  {entry.get('level','?')}: {entry.get('message','')[:300]}", flush=True)
        except Exception as e:
            print(f"console fetch failed: {e}", flush=True)
        drv.quit()
        httpd.shutdown()
        httpd.server_close()


if __name__ == "__main__":
    sys.exit(main())
