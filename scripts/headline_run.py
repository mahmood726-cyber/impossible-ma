# scripts/headline_run.py
"""Produce the BMJ Methods headline from MetaAudit severity signals.

Denominator: unique ma_id with >=1 CRITICAL audit flag.
Numerator (by case): how many of those classify as k1 / missing_se / adversarial
under the severity-priority rules in metaaudit_classifier.
"""
import argparse
import json
import sys
from pathlib import Path

import pandas as pd

from impossible_ma.metaaudit_adapter import find_corpus, load_corpus
from impossible_ma.metaaudit_classifier import classify_corpus

def _build_k_lookup(df: pd.DataFrame) -> dict[str, int]:
    """Extract k (study count) per ma_id from the 'underpowered' module detail strings.

    MetaAudit does not store k as a dedicated column. Heuristic: look at the
    'underpowered' module's detail string which typically embeds 'k=<int>' or
    'n_studies=<int>'. MAs without this information default to k=0, which
    biases classification toward k1 for any 'underpowered' flag.
    """
    import re
    k_pattern = re.compile(r"(?:k\s*=\s*|n_studies\s*=\s*)(\d+)", re.I)
    k_lookup: dict[str, int] = {}
    for ma_id, grp in df[df["module"] == "underpowered"].groupby("ma_id"):
        for detail in grp["detail"]:
            m = k_pattern.search(str(detail))
            if m:
                k_lookup[ma_id] = int(m.group(1))
                break
    return k_lookup

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--metaaudit-root", type=Path, default=None,
                    help="override: path to audit_results.csv")
    ap.add_argument("--output", type=Path, default=Path("scripts/headline_output.json"))
    args = ap.parse_args(argv)

    cand = [args.metaaudit_root] if args.metaaudit_root else None
    corpus_path = find_corpus(cand)
    df = load_corpus(corpus_path)

    k_lookup = _build_k_lookup(df)
    result = classify_corpus(df, k_lookup)

    crit = df[df["severity"] == "CRITICAL"]
    module_freq = crit["module"].value_counts().to_dict()

    out = {
        "corpus": str(corpus_path),
        "n_rows_total": int(len(df)),
        "n_ma_total": int(df["ma_id"].nunique()),
        "denominator_critical": int(result["denominator_critical"]),
        "numerator_by_case": {k: int(v) for k, v in result["counts"].items()},
        "numerator_total": int(sum(result["counts"].values())),
        "unclassified_count": int(len(result["unclassified_ma_ids"])),
        "critical_module_frequency": {k: int(v) for k, v in module_freq.items()},
        "k_lookup_coverage": int(len(k_lookup)),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))
    return 0

if __name__ == "__main__":
    sys.exit(main())
