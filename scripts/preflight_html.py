# scripts/preflight_html.py
"""Plan 2 preflight: HTML app prereqs."""
import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path

BROWSER_ROTATOR = Path(r"C:\Users\user\browser_rotator.py")


def check_selenium():
    spec = importlib.util.find_spec("selenium")
    if spec is None:
        return False, "selenium not installed. Install: pip install selenium"
    import selenium
    return True, f"OK: selenium {selenium.__version__}"


def check_browser_rotator():
    if not BROWSER_ROTATOR.exists():
        return False, f"browser_rotator.py not at {BROWSER_ROTATOR}"
    return True, f"OK: {BROWSER_ROTATOR}"


def check_chromedriver():
    chromedriver = shutil.which("chromedriver")
    if chromedriver:
        return True, f"OK: chromedriver at {chromedriver}"
    # Selenium 4 can manage drivers via Selenium Manager - succeed if selenium available
    return True, "Selenium Manager will fetch driver on demand"


def check_pip_wheel():
    try:
        r = subprocess.run(
            [sys.executable, "-m", "pip", "wheel", "--help"],
            capture_output=True, text=True, timeout=15,
        )
        if r.returncode != 0:
            return False, f"pip wheel failed: {r.stderr.strip()}"
        return True, "OK: pip wheel available"
    except Exception as e:
        return False, f"pip wheel invocation error: {e}"


def check_network_pyodide():
    try:
        import urllib.request
        with urllib.request.urlopen(
            "https://cdn.jsdelivr.net/pyodide/v0.27.7/full/pyodide.js",
            timeout=10,
        ) as r:
            if r.status == 200:
                return True, "OK: jsdelivr CDN reachable (Pyodide v0.27.7)"
        return False, f"CDN HTTP {r.status}"
    except Exception as e:
        return False, f"network/CDN check failed: {e}"


def main():
    checks = [
        ("selenium", check_selenium),
        ("browser_rotator.py", check_browser_rotator),
        ("chromedriver", check_chromedriver),
        ("pip wheel", check_pip_wheel),
        ("Pyodide CDN", check_network_pyodide),
    ]
    failed = 0
    for name, fn in checks:
        ok, msg = fn()
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {msg}")
        if not ok:
            failed += 1
    if failed:
        print(f"\n{failed} preflight check(s) failed. Fix before continuing.")
        sys.exit(1)
    print("\nAll Plan 2 preflight checks passed.")


if __name__ == "__main__":
    main()
