import json
from pathlib import Path

import pytest
from scipy import stats

from impossible_ma.missing_se import (
    p_to_se,
    ci_to_se,
    stat_to_se,
    figure_to_se,
    missing_se_envelope,
    MissingSeInput,
)
from impossible_ma.envelope import validate_envelope

FIXTURES = Path(__file__).parent / "fixtures"


# Route A
def test_p_to_se_two_sided():
    se = p_to_se(effect=0.5, p_value=0.04)
    assert abs(se - 0.2434) < 1e-3


def test_p_to_se_rejects_p_at_bounds():
    with pytest.raises(ValueError):
        p_to_se(effect=0.5, p_value=0.0)
    with pytest.raises(ValueError):
        p_to_se(effect=0.5, p_value=1.0)


def test_p_to_se_rejects_zero_effect():
    with pytest.raises(ValueError, match="effect"):
        p_to_se(effect=0.0, p_value=0.05)


# Route B
def test_ci_to_se_normal_approx():
    se = ci_to_se(ci_lower=0.2, ci_upper=0.8, conf_level=0.95)
    assert abs(se - 0.1531) < 1e-3


def test_ci_to_se_t_correction():
    se = ci_to_se(ci_lower=0.2, ci_upper=0.8, conf_level=0.95, df=10)
    assert abs(se - 0.1347) < 1e-3


def test_ci_to_se_rejects_inverted_bounds():
    with pytest.raises(ValueError, match="ci_lower"):
        ci_to_se(ci_lower=0.8, ci_upper=0.2)


def test_ci_to_se_rejects_bad_conf_level():
    with pytest.raises(ValueError, match="conf_level"):
        ci_to_se(ci_lower=0.0, ci_upper=1.0, conf_level=1.5)


# Route C
def test_stat_to_se_z():
    se = stat_to_se(effect=0.4, statistic=2.5)
    assert abs(se - 0.16) < 1e-6


def test_stat_to_se_t_with_df():
    se = stat_to_se(effect=0.4, statistic=2.5, df=10)
    expected = 0.4 / stats.norm.ppf(1 - stats.t.sf(2.5, 10))
    assert abs(se - expected) < 1e-6


def test_stat_to_se_rejects_zero_statistic():
    with pytest.raises(ValueError, match="statistic"):
        stat_to_se(effect=0.4, statistic=0.0)


# Route D stub
def test_figure_to_se_is_stubbed_for_v1():
    with pytest.raises(NotImplementedError, match="v1.1"):
        figure_to_se(image_path="anything.png")


# Envelope
def test_missing_se_envelope_two_routes_agree():
    inp = MissingSeInput(
        effect=0.4,
        p_value=0.04,
        ci_lower=0.0,
        ci_upper=0.8,
    )
    env = missing_se_envelope(inp)
    validate_envelope(env)
    assert env.case == "missing_se"
    assert env.point is not None
    assert env.lower <= env.upper


def test_missing_se_envelope_single_route_gives_collapsed():
    inp = MissingSeInput(effect=0.4, p_value=0.05)
    env = missing_se_envelope(inp)
    assert env.case == "missing_se"
    assert env.lower == env.upper
    assert env.point is not None


def test_missing_se_envelope_no_routes_raises():
    inp = MissingSeInput(effect=0.4)
    with pytest.raises(ValueError, match="no SE route"):
        missing_se_envelope(inp)


def test_missing_se_envelope_disagreeing_routes_collapse_none():
    inp = MissingSeInput(
        effect=0.4,
        p_value=0.001,
        ci_lower=0.0,
        ci_upper=0.01,
    )
    env = missing_se_envelope(inp)
    assert env.point is None
    assert env.lower < env.upper
