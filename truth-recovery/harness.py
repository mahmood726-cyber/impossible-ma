"""
harness.py -- Wire impossible-ma's OWN kone_envelope against the seeded
known-truth k=1 DGP and MEASURE partial-identification bound coverage.

Question (per truth-recovery brief): when a comparison is "unpoolable" (k=1)
and the method returns BOUNDS [lower, upper] by borrowing from adjacent trials,
do those bounds CONTAIN the target trial's TRUE effect at the claimed rate, and
are they informative (not trivially wide)?

We compare three things per replicate:
  - envelope [lower, upper]      (the method under test: kone_envelope)
  - naive single-trial 95% CI    (no borrowing: target_estimate +/- 1.96*se)
A partial-ID envelope is only worth having if it covers the truth at least as
well as the naive CI while being INFORMATIVE relative to the borrowing range.

Run:  python truth-recovery/harness.py
"""
from __future__ import annotations
import sys, os
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from impossible_ma.kone import KoneInput, kone_envelope  # noqa: E402

sys.path.insert(0, os.path.dirname(__file__))
from dgp_k1 import make_scenario  # noqa: E402

Z = 1.959963984540054


def run(n_reps=4000, mu_true=-0.30, tau_true=0.15, n_adjacent=5, seed=20260614):
    rng = np.random.default_rng(seed)
    env_cover = 0
    naive_cover = 0
    env_widths = []
    naive_widths = []
    point_abs_err = []

    for _ in range(n_reps):
        tgt_est, tgt_se, theta, adjacent = make_scenario(
            rng, mu_true, tau_true, n_adjacent
        )
        env = kone_envelope(
            KoneInput(
                target_estimate=tgt_est,
                target_se=tgt_se,
                adjacent=adjacent,
                endpoint="continuous",
            )
        )
        if env.lower <= theta <= env.upper:
            env_cover += 1
        env_widths.append(env.upper - env.lower)
        if env.point is not None:
            point_abs_err.append(abs(env.point - theta))

        lo = tgt_est - Z * tgt_se
        hi = tgt_est + Z * tgt_se
        if lo <= theta <= hi:
            naive_cover += 1
        naive_widths.append(hi - lo)

    return {
        "n_reps": n_reps,
        "mu_true": mu_true,
        "tau_true": tau_true,
        "n_adjacent": n_adjacent,
        "envelope_coverage": env_cover / n_reps,
        "naive_ci_coverage": naive_cover / n_reps,
        "envelope_mean_width": float(np.mean(env_widths)),
        "naive_ci_mean_width": float(np.mean(naive_widths)),
        "width_ratio_env_over_naive": float(np.mean(env_widths) / np.mean(naive_widths)),
        "robust_point_rmse": float(np.sqrt(np.mean(np.square(point_abs_err)))) if point_abs_err else None,
        "n_with_point": len(point_abs_err),
    }


if __name__ == "__main__":
    import json
    res = run()
    print(json.dumps(res, indent=2))
