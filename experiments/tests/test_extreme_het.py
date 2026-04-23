import json
import math
from pathlib import Path

import pytest

from experiments.extreme_het import run

FIXTURES = Path(__file__).parents[1] / "fixtures" / "extreme_het.json"


def _case(name: str) -> dict:
    return json.loads(FIXTURES.read_text())[name]


def test_normal_refuses_point():
    env = run(_case("normal"))
    assert env.flavour == "extreme_het"
    assert env.point is None
    assert "refused" in env.min_info
    assert math.isfinite(env.lower) and math.isfinite(env.upper)


def test_tight_pools_with_point():
    env = run(_case("tight"))
    assert env.point is not None
    assert env.point == pytest.approx(0.30, abs=0.05)
    assert "pooled" in env.min_info


def test_unbounded_refuses_and_flags():
    env = run(_case("unbounded"))
    assert env.point is None
    # bounds come from study spread, not unbounded
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
