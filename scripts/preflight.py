# C:\Models\ImpossibleMA\scripts\preflight.py
"""Fail-closed preflight for ImpossibleMA. Run BEFORE any implementation work."""
import os
import sys
import shutil
import subprocess
from pathlib import Path

REQUIRED_METAAUDIT_COLS = {"review_id", "abstract", "methods", "conclusion"}
METAAUDIT_CANDIDATES = [
    Path(r"C:\MetaAudit\outputs\reviews.csv"),
    Path(r"D:\MetaAudit\outputs\reviews.csv"),
]

def check_metaaudit():
    for p in METAAUDIT_CANDIDATES:
        if p.exists():
            import pandas as pd
            try:
                df = pd.read_csv(p, nrows=5)
            except Exception as e:
                return False, f"Found {p} but could not read: {e}"
            missing = REQUIRED_METAAUDIT_COLS - set(df.columns)
            if missing:
                return False, f"{p} missing columns: {sorted(missing)}"
            return True, f"OK: {p} ({len(df.columns)} cols)"
    return False, f"No MetaAudit corpus at any of: {METAAUDIT_CANDIDATES}"

def check_hmac_key():
    if os.environ.get("TRUTHCERT_HMAC_KEY"):
        return True, "OK: TRUTHCERT_HMAC_KEY set in environment"
    keyfile = Path.home() / ".truthcert_key"
    if keyfile.exists() and keyfile.stat().st_size >= 32:
        return True, f"OK: {keyfile} exists (>= 32 bytes)"
    return False, (
        "No TRUTHCERT_HMAC_KEY env var and no ~/.truthcert_key file. "
        "Set one before running. Do NOT derive key from bundle contents."
    )

def check_r():
    rscript = shutil.which("Rscript") or r"C:\Program Files\R\R-4.5.2\bin\Rscript.exe"
    if not Path(rscript).exists():
        return False, f"Rscript not found at {rscript}"
    try:
        r = subprocess.run(
            [rscript, "-e", "cat(as.character(packageVersion('RBesT')), packageVersion('metafor'))"],
            capture_output=True, text=True, timeout=30,
        )
        if r.returncode != 0:
            return False, f"Rscript failed: {r.stderr.strip()}"
        return True, f"OK: {rscript} — {r.stdout.strip()}"
    except Exception as e:
        return False, f"Rscript invocation error: {e}"

def check_python_deps():
    missing = []
    for mod in ("scipy", "statsmodels", "pandas", "pytest", "hypothesis"):
        try:
            __import__(mod)
        except ImportError:
            missing.append(mod)
    if missing:
        return False, f"Missing Python packages: {missing}. Install with: pip install {' '.join(missing)}"
    return True, "OK: scipy, statsmodels, pandas, pytest, hypothesis all importable"

def main():
    checks = [
        ("Python dependencies", check_python_deps),
        ("MetaAudit corpus", check_metaaudit),
        ("TRUTHCERT_HMAC_KEY", check_hmac_key),
        ("R + RBesT + metafor", check_r),
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
    print("\nAll preflight checks passed.")

if __name__ == "__main__":
    main()
