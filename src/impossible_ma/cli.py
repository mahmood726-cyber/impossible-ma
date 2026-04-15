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
