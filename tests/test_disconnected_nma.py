import math

import pytest

from impossible_ma.disconnected_nma import run


def _case_normal() -> dict:
    return {
        "bubble_1": {
            "studies": [
                {"id": "b1s1", "treat_a": "A", "treat_b": "B", "effect": -0.35, "se": 0.12},
                {"id": "b1s2", "treat_a": "A", "treat_b": "B", "effect": -0.28, "se": 0.15},
            ],
            "anchor_treatment": "A",
        },
        "bubble_2": {
            "studies": [
                {"id": "b2s1", "treat_a": "C", "treat_b": "D", "effect": -0.40, "se": 0.14},
                {"id": "b2s2", "treat_a": "C", "treat_b": "D", "effect": -0.33, "se": 0.18},
            ],
            "anchor_treatment": "C",
        },
        "bridging": {"delta_log_odds": 0.3},
        "target_contrast": ["B", "D"],
    }


def _case_tight() -> dict:
    return {
        "bubble_1": {
            "studies": [
                {"id": "b1s1", "treat_a": "A", "treat_b": "B", "effect": -0.35, "se": 0.12},
            ],
            "anchor_treatment": "A",
        },
        "bubble_2": {
            "studies": [
                {"id": "b2s1", "treat_a": "C", "treat_b": "D", "effect": -0.40, "se": 0.14},
            ],
            "anchor_treatment": "C",
        },
        "bridging": {"delta_log_odds": 0.0},
        "target_contrast": ["B", "D"],
    }


def _case_unbounded() -> dict:
    return {
        "bubble_1": {
            "studies": [
                {"id": "b1s1", "treat_a": "A", "treat_b": "B", "effect": -0.35, "se": 0.12},
            ],
            "anchor_treatment": "A",
        },
        "bubble_2": {
            "studies": [
                {"id": "b2s1", "treat_a": "C", "treat_b": "D", "effect": -0.40, "se": 0.14},
            ],
            "anchor_treatment": "C",
        },
        "bridging": {"delta_log_odds": None},
        "target_contrast": ["B", "D"],
    }


def test_normal_bounded():
    env = run(_case_normal())
    assert env.case == "disconnected_nma"
    assert math.isfinite(env.upper)
    assert math.isfinite(env.lower)
    assert env.upper > env.lower


def test_tight_matches_classical():
    env = run(_case_tight())
    # delta=0, single-study bubbles: indirect contrast = d1 - d2 = -0.35 - (-0.40) = 0.05
    assert env.point is not None
    assert env.point == pytest.approx(0.05, abs=0.05)


def test_unbounded_flagged():
    env = run(_case_unbounded())
    assert math.isinf(env.upper)
    assert "unbounded" in env.min_info


def test_empty_bubble_raises():
    bad = {
        "bubble_1": {"studies": [], "anchor_treatment": "A"},
        "bubble_2": {
            "studies": [{"id": "x", "treat_a": "C", "treat_b": "D", "effect": 0.0, "se": 0.1}],
            "anchor_treatment": "C",
        },
        "bridging": {"delta_log_odds": 0.3},
        "target_contrast": ["B", "D"],
    }
    with pytest.raises(ValueError, match="bubble"):
        run(bad)
