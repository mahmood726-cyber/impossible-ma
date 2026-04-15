from pathlib import Path
import pandas as pd
import pytest
from impossible_ma.kone import fit_map_prior, KoneInput, kone_envelope
from impossible_ma.envelope import validate_envelope

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def adjacent():
    df = pd.read_csv(FIXTURES / "adjacent_trials.csv")
    return list(zip(df["estimate"], df["se"]))


def test_fit_map_prior_returns_mean_and_tau(adjacent):
    result = fit_map_prior(adjacent)
    assert -0.5 < result["mu"] < -0.15
    assert result["tau"] >= 0.0
    assert result["mu_se"] > 0.0


def test_fit_map_prior_requires_min_three_adjacent():
    with pytest.raises(ValueError, match="at least 3"):
        fit_map_prior([(0.1, 0.2), (0.2, 0.3)])


def test_kone_input_validates_endpoint():
    with pytest.raises(ValueError, match="endpoint"):
        KoneInput(
            target_estimate=0.0,
            target_se=0.1,
            adjacent=[(0.1, 0.2)] * 3,
            endpoint="bogus",
        )


def test_kone_envelope_produces_valid_envelope(adjacent):
    inp = KoneInput(
        target_estimate=-0.50,
        target_se=0.25,
        adjacent=adjacent,
        endpoint="binary",
    )
    env = kone_envelope(inp)
    validate_envelope(env)
    assert env.case == "k1"
    assert env.lower <= env.upper
    assert env.point is not None


def test_kone_envelope_vague_is_widest(adjacent):
    inp = KoneInput(
        target_estimate=-0.50,
        target_se=0.25,
        adjacent=adjacent,
        endpoint="binary",
    )
    env = kone_envelope(inp)
    vague_ci = env.case_specific["vague_ci"]
    full_ci = env.case_specific["full_borrowing_ci"]
    assert (vague_ci[1] - vague_ci[0]) >= (full_ci[1] - full_ci[0])


def test_kone_envelope_min_info_mentions_additional_trial(adjacent):
    inp = KoneInput(
        target_estimate=-0.50,
        target_se=0.25,
        adjacent=adjacent,
        endpoint="binary",
    )
    env = kone_envelope(inp)
    assert "additional trial" in env.min_info.lower() or "more trial" in env.min_info.lower()
