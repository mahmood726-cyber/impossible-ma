import math

import pytest

from impossible_ma.extreme_het import run


def _case_normal() -> dict:
    return {
        "studies": [
            {"id": "s1", "effect": -0.80, "se": 0.10},
            {"id": "s2", "effect": 0.70, "se": 0.10},
            {"id": "s3", "effect": -0.50, "se": 0.12},
            {"id": "s4", "effect": 0.90, "se": 0.11},
            {"id": "s5", "effect": -0.60, "se": 0.13},
        ],
        "thresholds": {"i2_refuse_point": 0.80, "tau_ratio_refuse": 2.0},
    }


def _case_tight() -> dict:
    return {
        "studies": [
            {"id": "s1", "effect": 0.30, "se": 0.08},
            {"id": "s2", "effect": 0.32, "se": 0.09},
            {"id": "s3", "effect": 0.28, "se": 0.10},
            {"id": "s4", "effect": 0.31, "se": 0.08},
            {"id": "s5", "effect": 0.29, "se": 0.09},
        ],
        "thresholds": {"i2_refuse_point": 0.80, "tau_ratio_refuse": 2.0},
    }


def _case_unbounded() -> dict:
    return {
        "studies": [
            {"id": "s1", "effect": -2.0, "se": 0.05},
            {"id": "s2", "effect": 2.0, "se": 0.05},
            {"id": "s3", "effect": -1.8, "se": 0.05},
            {"id": "s4", "effect": 1.9, "se": 0.05},
        ],
        "thresholds": {"i2_refuse_point": 0.80, "tau_ratio_refuse": 2.0},
    }


def test_normal_refuses_point():
    env = run(_case_normal())
    assert env.case == "extreme_het"
    assert env.point is None
    assert "refused" in env.min_info
    assert math.isfinite(env.lower) and math.isfinite(env.upper)


def test_tight_pools_with_point():
    env = run(_case_tight())
    assert env.point is not None
    assert env.point == pytest.approx(0.30, abs=0.05)
    assert "pooled" in env.min_info


def test_unbounded_refuses_and_flags():
    env = run(_case_unbounded())
    assert env.point is None
    assert math.isfinite(env.lower) and math.isfinite(env.upper)
    assert "refused" in env.min_info


def test_k_lt_3_raises():
    bad = {
        "studies": [
            {"id": "s1", "effect": 0.1, "se": 0.05},
            {"id": "s2", "effect": 0.2, "se": 0.05},
        ],
        "thresholds": {"i2_refuse_point": 0.80, "tau_ratio_refuse": 2.0},
    }
    with pytest.raises(ValueError, match="k"):
        run(bad)
