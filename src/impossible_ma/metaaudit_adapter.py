from pathlib import Path
import pandas as pd

PINNED_SCHEMA: tuple[str, ...] = ("ma_id", "module", "severity", "detail")

DEFAULT_CANDIDATES: list[Path] = [
    Path(r"C:\MetaAudit\results\audit_results.csv"),
    Path(r"D:\MetaAudit\results\audit_results.csv"),
]


class SchemaMismatchError(RuntimeError):
    """Raised when the MetaAudit corpus columns do not match PINNED_SCHEMA."""


def find_corpus(candidates: list[Path] | None = None) -> Path:
    cands = candidates if candidates is not None else DEFAULT_CANDIDATES
    for p in cands:
        if Path(p).exists():
            return Path(p)
    raise FileNotFoundError(
        f"No MetaAudit corpus found. Searched: {[str(c) for c in cands]}. "
        "Action: copy MetaAudit outputs to one of these paths, or pass a custom "
        "candidate list to find_corpus()."
    )


def load_corpus(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    missing = set(PINNED_SCHEMA) - set(df.columns)
    if missing:
        raise SchemaMismatchError(
            f"MetaAudit corpus at {path} missing columns: {sorted(missing)}. "
            f"Expected: {list(PINNED_SCHEMA)}. Got: {list(df.columns)}. "
            "Update PINNED_SCHEMA in metaaudit_adapter.py or re-export corpus."
        )
    return df
