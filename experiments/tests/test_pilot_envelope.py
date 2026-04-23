import math
import pytest

from experiments.pilot_envelope import PilotEnvelope


def _valid(**overrides):
    base = dict(
        lower=-1.0,
        upper=1.0,
        point=0.0,
        min_info="ok",
        assumptions={},
        case="tight",
        flavour="disconnected_nma",
    )
    base.update(overrides)
    return PilotEnvelope(**base)


def test_lower_gt_upper_raises():
    with pytest.raises(ValueError, match="lower"):
        _valid(lower=2.0, upper=1.0)


def test_point_outside_bounds_raises():
    with pytest.raises(ValueError, match="outside"):
        _valid(lower=0.0, upper=1.0, point=2.0)


def test_empty_min_info_raises():
    with pytest.raises(ValueError, match="min_info"):
        _valid(min_info="")


def test_invalid_flavour_raises():
    with pytest.raises(ValueError, match="flavour"):
        _valid(flavour="not_a_flavour")


def test_upper_inf_without_unbounded_raises():
    with pytest.raises(ValueError, match="unbounded"):
        _valid(upper=math.inf, point=None, min_info="no flag here")


def test_to_possibility_envelope_raises():
    env = _valid()
    with pytest.raises(NotImplementedError, match="promotion"):
        env.to_possibility_envelope()
