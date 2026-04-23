import json
import math
from pathlib import Path

import pytest

from experiments.disconnected_nma import run

FIXTURES = Path(__file__).parents[1] / "fixtures" / "disconnected_nma.json"


def _case(name: str) -> dict:
    return json.loads(FIXTURES.read_text())[name]


def test_normal_bounded():
    env = run(_case("normal"))
    assert env.flavour == "disconnected_nma"
    assert math.isfinite(env.upper)
    assert math.isfinite(env.lower)
    assert env.upper > env.lower


def test_tight_matches_classical():
    env = run(_case("tight"))
    # delta=0, single-study bubbles: d_BD = -(-0.35) - (-0.40) = 0.05
    # (anchor-gap = 0 closes indirect contrast)
    assert env.point is not None
    assert env.point == pytest.approx(0.05, abs=0.05)


def test_unbounded_flagged():
    env = run(_case("unbounded"))
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
