"""Batch CLI for ImpossibleMA. Reads case-specific JSON, emits envelope JSON."""
import argparse
import json
import sys
from dataclasses import asdict

import pandas as pd

from .kone import KoneInput, kone_envelope
from .missing_se import MissingSeInput, missing_se_envelope
from .adversarial import adversarial_envelope
from .truthcert import sign_bundle


def _run_k1(payload: dict) -> dict:
    inp = KoneInput(
        target_estimate=payload["target_estimate"],
        target_se=payload["target_se"],
        adjacent=[tuple(a) for a in payload["adjacent"]],
        endpoint=payload["endpoint"],
    )
    env = kone_envelope(inp)
    return _envelope_to_dict(env)


def _run_missing_se(payload: dict) -> dict:
    # Route-D payload: figure extraction — multi-row output.
    if payload.get("route") == "D":
        from pathlib import Path
        from .missing_se import (
            Calibration, RowClick, build_figure_bundle,
        )
        from .truthcert import sign_bundle
        from dataclasses import asdict
        img_bytes = Path(payload["image"]).read_bytes()
        cal_d = payload["calibration"]
        cal = Calibration(
            scale=cal_d["scale"],
            ref_pixel_1=cal_d["ref_pixel_1"],
            ref_value_1=cal_d["ref_value_1"],
            ref_pixel_2=cal_d["ref_pixel_2"],
            ref_value_2=cal_d["ref_value_2"],
        )
        rows = [RowClick(**r) for r in payload["rows"]]
        bundle = build_figure_bundle(
            img_bytes, cal, rows,
            conf_level=payload.get("conf_level", 0.95),
            engine_version=payload.get("engine_version", "0.1.1"),
        )
        out = {
            "bundle": json.loads(json.dumps(asdict(bundle), default=float)),
            "results": [
                json.loads(json.dumps(asdict(r), default=float))
                for r in bundle.results
            ],
        }
        if payload.get("sign"):
            out["signed"] = sign_bundle({"bundle": out["bundle"]})
        return out

    # Existing A/B/C path
    inp = MissingSeInput(**payload)
    env = missing_se_envelope(inp)
    return _envelope_to_dict(env)


def _run_adversarial(payload: dict) -> dict:
    df = pd.DataFrame(payload["studies"])
    env = adversarial_envelope(df)
    return _envelope_to_dict(env)


def _envelope_to_dict(env) -> dict:
    d = asdict(env)
    return json.loads(json.dumps(d, default=float))


_RUNNERS = {
    "k1": _run_k1,
    "missing_se": _run_missing_se,
    "adversarial": _run_adversarial,
}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="impossible-ma")
    ap.add_argument("case", choices=list(_RUNNERS))
    ap.add_argument("input_json")
    ap.add_argument("--output", "-o", default="-", help="output path ('-' for stdout)")
    ap.add_argument("--sign", action="store_true", help="wrap output in TruthCert bundle")
    args = ap.parse_args(argv)

    with open(args.input_json) as f:
        payload = json.load(f)
    result = _RUNNERS[args.case](payload)
    if args.sign:
        result = sign_bundle(result)
    text = json.dumps(result, indent=2)
    if args.output == "-":
        print(text)
    else:
        with open(args.output, "w") as f:
            f.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
