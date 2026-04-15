import pandas as pd
import pytest
from impossible_ma.metaaudit_adapter import (
    find_corpus, load_corpus, PINNED_SCHEMA, SchemaMismatchError,
)

def test_find_corpus_returns_existing_path(tmp_path):
    fake = tmp_path / "audit_results.csv"
    pd.DataFrame({c: [""] for c in PINNED_SCHEMA}).to_csv(fake, index=False)
    assert find_corpus(candidates=[fake]) == fake

def test_find_corpus_raises_when_none_exist(tmp_path):
    with pytest.raises(FileNotFoundError, match="No MetaAudit corpus"):
        find_corpus(candidates=[tmp_path / "does_not_exist.csv"])

def test_load_corpus_accepts_pinned_schema(tmp_path):
    p = tmp_path / "audit_results.csv"
    pd.DataFrame({c: ["x"] for c in PINNED_SCHEMA}).to_csv(p, index=False)
    df = load_corpus(p)
    assert set(df.columns) >= set(PINNED_SCHEMA)

def test_load_corpus_rejects_missing_column(tmp_path):
    p = tmp_path / "audit_results.csv"
    cols = [c for c in PINNED_SCHEMA if c != "severity"]
    pd.DataFrame({c: ["x"] for c in cols}).to_csv(p, index=False)
    with pytest.raises(SchemaMismatchError) as exc:
        load_corpus(p)
    assert "severity" in str(exc.value)

def test_load_real_corpus_if_available():
    from pathlib import Path
    real = Path(r"C:\MetaAudit\results\audit_results.csv")
    if not real.exists():
        pytest.skip("real MetaAudit corpus not on disk")
    df = load_corpus(real)
    assert len(df) > 0
    assert df["ma_id"].nunique() > 100
    assert {"PASS", "CRITICAL"} <= set(df["severity"].unique())
