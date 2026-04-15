import pandas as pd
import pytest
from impossible_ma.metaaudit_classifier import (
    critical_modules, classify_ma, classify_corpus,
)

def _row(ma_id, module, severity, detail=""):
    return {"ma_id": ma_id, "module": module, "severity": severity, "detail": detail}

def test_critical_modules_extracts_only_critical():
    df = pd.DataFrame([
        _row("A1", "fragility", "CRITICAL"),
        _row("A1", "pub_bias", "WARNING"),
        _row("A1", "integrity", "PASS"),
    ])
    out = critical_modules(df, "A1")
    assert out == {"fragility"}

def test_classify_ma_integrity_takes_priority():
    df = pd.DataFrame([
        _row("M1", "integrity", "CRITICAL"),
        _row("M1", "fragility", "CRITICAL"),
    ])
    assert classify_ma(df, "M1", k_studies=5) == "missing_se"

def test_classify_ma_underpowered_k_small_is_k1():
    df = pd.DataFrame([_row("M2", "underpowered", "CRITICAL")])
    assert classify_ma(df, "M2", k_studies=2) == "k1"

def test_classify_ma_underpowered_k_large_is_adversarial():
    df = pd.DataFrame([_row("M3", "underpowered", "CRITICAL")])
    assert classify_ma(df, "M3", k_studies=8) == "adversarial"

def test_classify_ma_fragility_is_adversarial():
    df = pd.DataFrame([_row("M4", "fragility", "CRITICAL")])
    assert classify_ma(df, "M4", k_studies=6) == "adversarial"

def test_classify_ma_excess_sig_is_adversarial():
    df = pd.DataFrame([_row("M5", "excess_sig", "CRITICAL")])
    assert classify_ma(df, "M5", k_studies=10) == "adversarial"

def test_classify_ma_no_critical_returns_none():
    df = pd.DataFrame([
        _row("M6", "fragility", "PASS"),
        _row("M6", "underpowered", "WARNING"),
    ])
    assert classify_ma(df, "M6", k_studies=5) is None

def test_classify_ma_unknown_critical_module_returns_none():
    df = pd.DataFrame([_row("M7", "overlap", "CRITICAL")])
    assert classify_ma(df, "M7", k_studies=5) is None

def test_classify_corpus_returns_counter():
    df = pd.DataFrame([
        _row("A", "fragility", "CRITICAL"),
        _row("B", "integrity", "CRITICAL"),
        _row("C", "underpowered", "CRITICAL"),
        _row("D", "overlap", "CRITICAL"),
        _row("E", "fragility", "PASS"),
    ])
    k_lookup = {"A": 5, "B": 4, "C": 2, "D": 3, "E": 9}
    result = classify_corpus(df, k_lookup)
    assert result["classified"]["A"] == "adversarial"
    assert result["classified"]["B"] == "missing_se"
    assert result["classified"]["C"] == "k1"
    assert "D" not in result["classified"]
    assert "E" not in result["classified"]
    assert result["counts"]["adversarial"] == 1
    assert result["counts"]["missing_se"] == 1
    assert result["counts"]["k1"] == 1
    assert result["denominator_critical"] == 4
