"""Export three figures from impossible-ma.html for the manuscripts.

Loads the HTML app in headless Chrome, runs the three case modules with
their named built-in datasets, calls Plotly.toImage(format='svg'), writes
the SVGs to paper/figures/.
"""
import http.server
import os
import socketserver
import sys
import threading
from pathlib import Path
from urllib.parse import unquote

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "impossible-ma.html"
FIG_DIR = ROOT / "paper" / "figures"
PORT = 8780
PAGE_URL = f"http://localhost:{PORT}/impossible-ma.html"
PAGE_READY_TIMEOUT = 480

# (tab hash, dataset value, viz div id, output filename)
EXPORTS = [
    ("k1", "rare_hf", "k1-viz", "kone_rare_hf.svg"),
    ("missing_se", "multi_consistent", "ms-viz", "missing_se_multi.svg"),
    ("adversarial", "pcsk9", "adv-viz", "adversarial_pcsk9.svg"),
]

# Map tab name to the prefix used by the HTML's element IDs
PREFIX = {"k1": "k1", "missing_se": "ms", "adversarial": "adv"}


def _load_dataset_and_run(driver, tab, dataset, run_timeout):
    p = PREFIX[tab]
    driver.execute_script(f"location.hash = '#{tab}';")
    Select(driver.find_element(By.ID, f"{p}-dataset")).select_by_value(dataset)
    driver.find_element(By.ID, f"{p}-load").click()
    WebDriverWait(driver, 5).until(
        lambda d: not d.find_element(By.ID, f"{p}-run").get_attribute("disabled")
    )
    driver.find_element(By.ID, f"{p}-run").click()
    WebDriverWait(driver, run_timeout).until(
        lambda d: not d.find_element(By.ID, f"{p}-result").get_attribute("hidden")
    )


def _export_svg(driver, viz_id, out_path):
    data_uri = driver.execute_async_script(f"""
const cb = arguments[arguments.length - 1];
Plotly.toImage(document.getElementById('{viz_id}'), {{format: 'svg', width: 800, height: 400}})
  .then(uri => cb(uri))
  .catch(err => cb('ERROR:' + err.message));
    """)
    if data_uri.startswith("ERROR:"):
        raise RuntimeError(f"Plotly.toImage failed for {viz_id}: {data_uri[6:]}")
    if not data_uri.startswith("data:image/svg+xml,"):
        raise RuntimeError(f"Unexpected data URI prefix: {data_uri[:40]}")
    svg = unquote(data_uri[len("data:image/svg+xml,"):])
    out_path.write_text(svg, encoding="utf-8")


def main() -> int:
    if not HTML.exists():
        print(f"FAIL: {HTML} missing - run `python scripts/build_html.py` first")
        return 1
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    cwd_before = os.getcwd()
    os.chdir(ROOT)
    httpd = socketserver.TCPServer(("", PORT), http.server.SimpleHTTPRequestHandler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        opts = Options()
        opts.add_argument("--headless=new")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--window-size=1400,900")
        drv = webdriver.Chrome(options=opts)
        try:
            print(f"  Loading {PAGE_URL} (Pyodide cold-load may take 3-8 min)...")
            drv.get(PAGE_URL)
            import time as _time
            t0 = _time.time()
            while True:
                ready = drv.execute_script(
                    "return window.PYODIDE_READY === true || window.PYODIDE_LOAD_ERROR != null"
                )
                if ready:
                    break
                elapsed = _time.time() - t0
                if elapsed > PAGE_READY_TIMEOUT:
                    splash = drv.execute_script(
                        "const el = document.getElementById('splash-status'); return el ? el.textContent : 'n/a';"
                    )
                    print(f"FAIL: Pyodide did not become ready within {PAGE_READY_TIMEOUT}s. Last splash: {splash!r}")
                    return 1
                status_msg = drv.execute_script(
                    "const el = document.getElementById('splash-status'); return el ? el.textContent : '';"
                )
                print(f"  [{elapsed:.0f}s] {status_msg}")
                _time.sleep(15)
            print(f"  Pyodide ready in {_time.time() - t0:.0f}s")
            err = drv.execute_script("return window.PYODIDE_LOAD_ERROR")
            if err:
                print(f"FAIL: Pyodide load error: {err}")
                return 1
            for tab, dataset, viz_id, fname in EXPORTS:
                run_to = 90 if tab == "adversarial" else 30
                _load_dataset_and_run(drv, tab, dataset, run_to)
                out = FIG_DIR / fname
                _export_svg(drv, viz_id, out)
                print(f"  wrote {out} ({out.stat().st_size} bytes)")
        finally:
            drv.quit()
    finally:
        httpd.shutdown(); httpd.server_close(); os.chdir(cwd_before)
    return 0


if __name__ == "__main__":
    sys.exit(main())
