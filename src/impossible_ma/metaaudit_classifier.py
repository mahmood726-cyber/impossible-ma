"""MetaAudit severity-signal classifier.

Maps (ma_id, critical_modules, k_studies) -> ImpossibleMA case, using the
priority order documented in spec 2026-04-15-impossibleMA-design.md sec 5.
"""
from collections import Counter
from typing import Literal
import pandas as pd

Case = Literal["k1", "missing_se", "adversarial"]

K_UNDERPOWERED_THRESHOLD = 2  # k <= this triggers k1 branch

def critical_modules(df: pd.DataFrame, ma_id: str) -> set[str]:
    """Return the set of module names with severity='CRITICAL' for ma_id."""
    sub = df[(df["ma_id"] == ma_id) & (df["severity"] == "CRITICAL")]
    return set(sub["module"].unique())

def classify_ma(df: pd.DataFrame, ma_id: str, k_studies: int) -> Case | None:
    """Apply the severity-priority rules. Returns None if no critical flag maps to a case."""
    crit = critical_modules(df, ma_id)
    # Priority order: integrity -> underpowered(k<=T) -> fragility -> excess_sig -> underpowered(k>T)
    if "integrity" in crit:
        return "missing_se"
    if "underpowered" in crit and k_studies <= K_UNDERPOWERED_THRESHOLD:
        return "k1"
    if "fragility" in crit:
        return "adversarial"
    if "excess_sig" in crit:
        return "adversarial"
    if "underpowered" in crit:
        return "adversarial"
    return None

def classify_corpus(df: pd.DataFrame, k_lookup: dict[str, int]) -> dict:
    """Classify every ma_id in the corpus.

    Returns dict with:
      - classified: {ma_id: case} for MAs with a case assignment
      - counts: Counter[case]
      - denominator_critical: count of unique ma_id with >=1 CRITICAL flag
      - unclassified_ma_ids: list[str] for MAs with CRITICAL but no mapped case
    """
    ma_ids_with_critical = set(
        df.loc[df["severity"] == "CRITICAL", "ma_id"].unique()
    )
    classified: dict[str, Case] = {}
    unclassified: list[str] = []
    for ma_id in ma_ids_with_critical:
        k = k_lookup.get(ma_id, 0)
        case = classify_ma(df, ma_id, k)
        if case is None:
            unclassified.append(ma_id)
        else:
            classified[ma_id] = case
    return {
        "classified": classified,
        "counts": Counter(classified.values()),
        "denominator_critical": len(ma_ids_with_critical),
        "unclassified_ma_ids": unclassified,
    }
