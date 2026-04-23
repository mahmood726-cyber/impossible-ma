import json
import math
from pathlib import Path

import pytest

from experiments.cross_framing import run

FIXTURES = Path(__file__).parents[1] / "fixtures" / "cross_framing.json"


def _case(name: str) -> dict:
    return json.loads(FIXTURES.read_text())[name]


def test_normal_bounded_with_point():
    env = run(_case("normal"))
    assert env.flavour == "cross_framing"
    assert env.point is not None
    assert math.isfinite(env.upper) and math.isfinite(env.lower)


def test_tight_all_continuous_matches_classical():
    env = run(_case("tight"))
    # all-continuous tight case: pooled SMD should be around mean_diff / pooled_sd ~ -3.0/12.0 = -0.25
    assert env.point is not None
    assert env.point == pytest.approx(-0.25, abs=0.1)


def test_unbounded_conflicting_signs_wide_envelope():
    env = run(_case("unbounded"))
    assert env.point is not None
    width = env.upper - env.lower
    assert width > 0.5  # wide envelope from conflicting signs + high conversion CV


def test_unknown_frame_raises():
    bad = {
        "studies": [{"id": "s1", "frame": "vibes", "x": 1.0}],
        "conversion_uncertainty": {},
    }
    with pytest.raises(ValueError, match="frame"):
        run(bad)
