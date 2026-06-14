"""
dgp_k1.py -- Standalone seeded known-truth DGP for the "k=1 unpoolable" case
that impossible-ma's kone_envelope targets.

Scenario: a Cochrane comparison has exactly ONE trial on the target population
(so a random-effects pool cannot be formed -- "unpoolable" for k=1), but there
are >=3 ADJACENT trials in related populations. The method borrows strength
from the adjacent trials via a MAP prior and returns a *possibility envelope*
[lower, upper] spanning no-borrowing (vague prior) to full-borrowing
(informative prior).

The honest partial-identification test: the target trial has a KNOWN true
effect theta_target. We observe only a noisy estimate of it (target_estimate
+/- target_se) plus the adjacent trials. Does the envelope [lower, upper]
CONTAIN theta_target at the claimed rate, and is it informative (narrower than
trivial)?

Truth model (random-effects family, shared by target + adjacent trials):
    theta_i ~ Normal(mu_true, tau_true^2)          # true per-trial effect
    yhat_i  ~ Normal(theta_i, se_i^2)              # observed estimate
The target's theta is drawn from the SAME family, so borrowing toward the
adjacent mean is legitimate -- this is the regime the method claims to serve.

Seeded -> fully reproducible. Depends only on numpy.
"""
from __future__ import annotations
import numpy as np


def draw_se(rng, lo=0.10, hi=0.45):
    """Log-uniform SE, typical of trial-level log-effect SEs."""
    return float(np.exp(rng.uniform(np.log(lo), np.log(hi))))


def make_scenario(rng, mu_true, tau_true, n_adjacent=5):
    """One replicate. Returns (target_estimate, target_se, theta_target,
    adjacent[list of (yhat, se)]).

    theta_target is the GROUND TRUTH the envelope must contain.
    """
    # adjacent trials: true effects from the family, observed with noise
    adjacent = []
    for _ in range(n_adjacent):
        se = draw_se(rng)
        theta = rng.normal(mu_true, tau_true)
        yhat = rng.normal(theta, se)
        adjacent.append((float(yhat), float(se)))

    # target trial: its true effect is ALSO from the family (exchangeable)
    target_se = draw_se(rng)
    theta_target = float(rng.normal(mu_true, tau_true))
    target_estimate = float(rng.normal(theta_target, target_se))

    return target_estimate, target_se, theta_target, adjacent
