import json
from pathlib import Path

import pandas as pd
import pytest

from impossible_ma.adversarial import (
    Rule,
    default_rule_grid,
    enumerate_rules,
    apply_rule,
    feasible_pools,
    pool_reml_hksj,
    adversarial_envelope,
    MAX_POOLS,
)
from impossible_ma.envelope import validate_envelope

FIXTURES = Path(__file__).parent / "fixtures"


def _toy_studies() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "study": [f"S{i}" for i in range(10)],
            "estimate": [0.1, -0.1, 0.2, -0.3, 0.05, 0.15, -0.2, 0.3, -0.05, 0.1],
            "se": [0.1, 0.15, 0.2, 0.1, 0.2, 0.12, 0.1, 0.15, 0.08, 0.11],
            "rob": ["low", "low", "some", "moderate", "high", "low", "some", "moderate", "low", "high"],
            "n": [100, 50, 300, 80, 40, 200, 60, 250, 150, 45],
            "followup": [12, 6, 24, 9, 3, 18, 6, 15, 12, 3],
            "language": ["english"] * 8 + ["other"] * 2,
            "pub_type": ["peer"] * 9 + ["grey"],
        }
    )


# Task 16 — grid enumeration
def test_default_rule_grid_has_expected_shape():
    g = default_rule_grid()
    assert set(g.keys()) == {"rob_cutoff", "n_floor", "followup_floor", "language", "pub_type"}
    assert len(g["rob_cutoff"]) == 5
    assert len(g["n_floor"]) == 3
    assert len(g["followup_floor"]) == 3
    assert len(g["language"]) == 2
    assert len(g["pub_type"]) == 2


def test_enumerate_rules_cardinality_matches_grid():
    g = default_rule_grid()
    rules = list(enumerate_rules(g))
    assert len(rules) == 5 * 3 * 3 * 2 * 2


def test_rule_is_hashable():
    g = default_rule_grid()
    r = next(iter(enumerate_rules(g)))
    _ = {r}


# Task 17 — pool filter
def test_apply_rule_filters_out_high_rob():
    df = _toy_studies()
    rule = Rule("low", 0, 0, "any", "any")
    out = apply_rule(df, rule)
    assert (out["rob"] == "low").all()


def test_apply_rule_respects_n_floor():
    df = _toy_studies()
    rule = Rule("any", 100, 0, "any", "any")
    out = apply_rule(df, rule)
    assert (out["n"] >= 100).all()


def test_feasible_pools_requires_k_ge_3():
    df = _toy_studies()
    grid = default_rule_grid()
    pools = list(feasible_pools(df, enumerate_rules(grid)))
    for _rule, pool in pools:
        assert len(pool) >= 3


def test_feasible_pools_caps_at_max():
    df = _toy_studies()
    grid = default_rule_grid()
    pools = list(feasible_pools(df, enumerate_rules(grid)))
    assert len(pools) <= MAX_POOLS


# Task 18 — pooling
def test_pool_reml_hksj_returns_estimate_and_ci():
    df = _toy_studies().head(5)
    res = pool_reml_hksj(df["estimate"].to_numpy(), df["se"].to_numpy())
    assert "estimate" in res and "ci_lower" in res and "ci_upper" in res
    assert res["ci_lower"] < res["estimate"] < res["ci_upper"]
    assert "tau2" in res and res["tau2"] >= 0
    assert res["k"] == 5


def test_pool_reml_hksj_applies_floor_when_q_small():
    y = [0.1, 0.11, 0.09, 0.10, 0.105]
    se = [0.05, 0.05, 0.05, 0.05, 0.05]
    res = pool_reml_hksj(y, se)
    assert "hksj_floor_applied" in res


# Task 19 — envelope
def test_adversarial_envelope_contains_full_data_reml():
    df = _toy_studies()
    env = adversarial_envelope(df)
    validate_envelope(env)
    assert env.case == "adversarial"
    assert env.point is None
    full = env.case_specific["full_data_reml"]
    assert env.lower <= full["estimate"] <= env.upper


def test_adversarial_envelope_flags_no_significant_pool():
    df = _toy_studies().copy()
    df["estimate"] = 0.001
    df["se"] = 0.5
    env = adversarial_envelope(df)
    assert env.case_specific["no_significant_pool"] is True


def test_adversarial_envelope_exports_rule_tuples_for_extremes():
    df = _toy_studies()
    env = adversarial_envelope(df)
    assert "lower_rule" in env.case_specific
    assert "upper_rule" in env.case_specific
    assert isinstance(env.case_specific["lower_rule"], str)


def test_adversarial_regression():
    b = json.loads((FIXTURES / "adversarial_baseline.json").read_text())
    df = pd.DataFrame(b["studies"])
    env = adversarial_envelope(df)
    assert abs(env.lower - b["lower"]) < 1e-6
    assert abs(env.upper - b["upper"]) < 1e-6
    assert env.case_specific["n_pools"] == b["n_pools"]
    assert env.case_specific["no_significant_pool"] == b["no_significant_pool"]
    assert (
        abs(env.case_specific["full_data_reml"]["estimate"] - b["full_data_reml"]["estimate"])
        < 1e-6
    )
