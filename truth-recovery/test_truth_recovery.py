"""
Truth-recovery assertions for impossible-ma's kone_envelope (k=1 unpoolable
partial-identification bounds). Run: pytest truth-recovery/test_truth_recovery.py

These tests verify the HONEST claim of a partial-ID method: the bounds contain
the true effect at >= the claimed rate, AND remain informative (not trivially
wide). Everything is measured against the seeded known-truth DGP -- no
hand-entered numbers.
"""
import sys, os
import pytest

sys.path.insert(0, os.path.dirname(__file__))
from harness import run  # noqa: E402


@pytest.fixture(scope="module")
def base():
    return run(n_reps=4000, mu_true=-0.30, tau_true=0.15, seed=20260614)


def test_envelope_covers_truth_at_or_above_nominal(base):
    # Partial-ID bounds must contain the true effect at least as often as a
    # nominal 95% interval. (Measured ~0.98.)
    assert base["envelope_coverage"] >= 0.95


def test_envelope_at_least_as_good_as_naive(base):
    # Borrowing must not LOSE coverage relative to the no-borrowing naive CI.
    assert base["envelope_coverage"] >= base["naive_ci_coverage"] - 0.005


def test_envelope_is_informative_not_trivially_wide(base):
    # An honest partial-ID envelope is worthless if it just balloons. It must
    # stay close to the naive single-trial width (measured ~1.03x).
    assert base["width_ratio_env_over_naive"] < 1.30


def test_robust_point_recovers_true_effect(base):
    # The robust MAP-mixture point estimate should have small RMSE vs truth.
    assert base["robust_point_rmse"] is not None
    assert base["robust_point_rmse"] < 0.30


def test_coverage_holds_under_high_heterogeneity():
    # Even when adjacent trials are a poor guide (large tau), borrowing must
    # not destroy coverage of the target's true effect.
    r = run(n_reps=3000, tau_true=0.50, seed=4242)
    assert r["envelope_coverage"] >= 0.93
    assert r["width_ratio_env_over_naive"] < 1.30
