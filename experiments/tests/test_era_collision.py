import json
import math
from pathlib import Path

import pytest

from experiments.era_collision import run

FIXTURES = Path(__file__).parents[1] / "fixtures" / "era_collision.json"


def _case(name: str) -> dict:
    return json.loads(FIXTURES.read_text())[name]


def test_normal_bounded():
    env = run(_case("normal"))
    assert env.flavour == "era_collision"
    assert math.isfinite(env.upper) and math.isfinite(env.lower)
    assert env.upper > env.lower


def test_tight_beta_zero_matches_classical_pool():
    env = run(_case("tight"))
    # beta_lo == beta_hi == 0: classical FE pool, approx mean log-HR ~ -0.235
    assert env.point is not None
    assert env.point == pytest.approx(-0.235, abs=0.05)


def test_unbounded_wide_beta_widens_envelope():
    env = run(_case("unbounded"))
    width = env.upper - env.lower
    # beta_range [-5, 5] with 2-era fixture drives wide envelope
    assert width > 1.0


def test_missing_era_label_raises():
    bad = {
        "studies": [
            {"id": "s1", "log_hr": -0.25, "se": 0.08, "control_rate_per_year": 0.15}
        ],
        "bridging": {"beta_range": [0.0, 0.0]},
    }
    with pytest.raises(ValueError, match="era"):
        run(bad)
