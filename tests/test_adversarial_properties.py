import numpy as np
import pandas as pd
from hypothesis import given, settings, strategies as st

from impossible_ma.adversarial import adversarial_envelope, default_rule_grid


def _random_studies(n: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    return pd.DataFrame(
        {
            "study": [f"S{i}" for i in range(n)],
            "estimate": rng.normal(0, 0.3, size=n),
            "se": rng.uniform(0.05, 0.3, size=n),
            "rob": rng.choice(["low", "some", "moderate", "high"], size=n),
            "n": rng.integers(30, 500, size=n),
            "followup": rng.integers(1, 36, size=n),
            "language": rng.choice(["english", "other"], size=n, p=[0.8, 0.2]),
            "pub_type": rng.choice(["peer", "grey"], size=n, p=[0.9, 0.1]),
        }
    )


@given(n=st.integers(min_value=8, max_value=20), seed=st.integers(0, 1000))
@settings(deadline=10000, max_examples=15)
def test_envelope_contains_full_data_reml(n, seed):
    df = _random_studies(n, seed)
    try:
        env = adversarial_envelope(df)
    except ValueError:
        return  # not enough studies for any pool
    full = env.case_specific["full_data_reml"]
    assert env.lower <= full["estimate"] <= env.upper


@given(seed=st.integers(0, 1000))
@settings(deadline=10000, max_examples=8)
def test_envelope_monotonicity_adding_rule_never_narrows(seed):
    df = _random_studies(15, seed)
    grid_small = default_rule_grid()
    # "Add a rule option" = add another rob_cutoff slot; the extra slot is a
    # duplicate so the feasible pools list is a superset.
    grid_big = dict(grid_small)
    grid_big["rob_cutoff"] = list(grid_small["rob_cutoff"]) + ["low"]
    try:
        env_small = adversarial_envelope(df, grid_small)
        env_big = adversarial_envelope(df, grid_big)
    except ValueError:
        return
    width_small = env_small.upper - env_small.lower
    width_big = env_big.upper - env_big.lower
    assert width_big >= width_small - 1e-9
