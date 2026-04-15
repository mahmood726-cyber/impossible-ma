"""Build impossible-ma.html by embedding the latest impossible_ma wheel.

Reads the latest .whl from dist/, base64-encodes it, substitutes
__WHEEL_BASE64__ in impossible-ma.html.template, writes impossible-ma.html.
"""
import argparse
import base64
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "impossible-ma.html.template"
OUTPUT = ROOT / "impossible-ma.html"
DIST = ROOT / "dist"


def build_wheel() -> Path:
    DIST.mkdir(exist_ok=True)
    for w in DIST.glob("impossible_ma-*.whl"):
        w.unlink()
    r = subprocess.run(
        [sys.executable, "-m", "pip", "wheel", str(ROOT), "-w", str(DIST), "--no-deps"],
        capture_output=True, text=True, check=False,
    )
    if r.returncode != 0:
        raise RuntimeError(f"pip wheel failed:\n{r.stderr}")
    wheels = sorted(DIST.glob("impossible_ma-*.whl"))
    if not wheels:
        raise RuntimeError("No wheel produced in dist/")
    return wheels[-1]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wheel", type=Path, help="use this wheel instead of building")
    args = ap.parse_args(argv)

    wheel = args.wheel if args.wheel else build_wheel()
    print(f"Using wheel: {wheel} ({wheel.stat().st_size} bytes)")

    template = TEMPLATE.read_text(encoding="utf-8")
    if "__WHEEL_BASE64__" not in template:
        raise RuntimeError(f"template missing __WHEEL_BASE64__ placeholder: {TEMPLATE}")

    b64 = base64.b64encode(wheel.read_bytes()).decode("ascii")
    output = template.replace("__WHEEL_BASE64__", b64)
    OUTPUT.write_text(output, encoding="utf-8")
    print(f"Wrote {OUTPUT} ({len(output)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
