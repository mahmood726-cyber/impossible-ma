from pathlib import Path
import pandas as pd
import pytest
from impossible_ma.kone import fit_map_prior, KoneInput

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
