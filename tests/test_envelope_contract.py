import pytest
from impossible_ma.envelope import PossibilityEnvelope, validate_envelope


def test_envelope_basic_construction():
    env = PossibilityEnvelope(
        lower=-0.5, upper=0.2, point=None,
        min_info="one more trial",
        assumptions={"prior": "vague"},
        case="k1",
        case_specific={},
    )
    assert env.lower <= env.upper
    assert env.case == "k1"


def test_envelope_lower_must_not_exceed_upper():
    with pytest.raises(ValueError, match="lower.*upper"):
        PossibilityEnvelope(
            lower=0.5, upper=0.2, point=None,
            min_info="x", assumptions={}, case="k1", case_specific={},
        )


def test_envelope_case_must_be_valid():
    with pytest.raises(ValueError, match="case"):
        PossibilityEnvelope(
            lower=0.0, upper=1.0, point=None,
            min_info="x", assumptions={}, case="not_a_case", case_specific={},
        )


def test_validate_envelope_accepts_valid():
    env = PossibilityEnvelope(
        lower=-0.1, upper=0.1, point=0.0,
        min_info="x", assumptions={}, case="missing_se", case_specific={},
    )
    validate_envelope(env)  # should not raise


def test_validate_envelope_rejects_point_outside_range():
    env = PossibilityEnvelope.__new__(PossibilityEnvelope)
    env.lower = 0.0; env.upper = 1.0; env.point = 2.0
    env.min_info = "x"; env.assumptions = {}; env.case = "k1"; env.case_specific = {}
    with pytest.raises(ValueError, match="point.*outside"):
        validate_envelope(env)
