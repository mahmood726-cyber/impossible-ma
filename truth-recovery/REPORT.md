# Truth-Recovery Validation -- impossible-ma

**Repo:** mahmood726-cyber/impossible-ma
**Method under test:** impossible_ma.kone.kone_envelope (k=1 "unpoolable" partial-identification possibility envelope).
**Date:** 2026-06-14

## Verdict: VALIDATED (genuine partial-identification methods engine)

impossible-ma is a real Python methods package (src/impossible_ma/), not a stub or dashboard. Stated purpose -- "bounded synthesis for Cochrane MAs declared unpoolable" -- is implemented in three partial-ID engines: kone.py (k=1, borrow from adjacent trials), missing_se.py (reconstruct missing SE), adversarial.py (envelope over feasible pooling rules). We validated the k=1 core: the canonical "a point estimate can't be formed, so return bounds" case.

## How it was tested

Honest test of a partial-ID method: do the bounds contain the truth, and are they informative (not trivially wide)?

- DGP (dgp_k1.py, seeded, numpy-only): random-effects family theta_i ~ N(mu_true, tau_true^2), yhat_i ~ N(theta_i, se_i^2). Target trial is k=1 (unpoolable) with KNOWN true effect theta_target drawn from the same family; we observe only a noisy estimate plus >=3 adjacent trials. Borrowing toward the adjacent mean is legitimate -- the regime the method claims to serve.
- Harness (harness.py): wires the repo's OWN kone_envelope; measures whether [lower, upper] contains theta_target, versus a no-borrowing naive single-trial 95% CI, plus robust MAP-mixture point RMSE.

## Measured results

Primary scenario (mu_true=-0.30, tau_true=0.15, n_adjacent=5, 4000 reps):

| metric | value |
|---|---|
| envelope bound coverage of true effect | 0.980 |
| naive single-trial 95% CI coverage | 0.948 |
| envelope width / naive CI width | 1.03x (informative) |
| robust MAP-mixture point RMSE | 0.173 |

Heterogeneity sweep (3000 reps each):

| tau_true | env coverage | naive coverage | width ratio | point RMSE |
|---|---|---|---|---|
| 0.05 | 0.990 | 0.958 | 1.019 | 0.157 |
| 0.15 | 0.984 | 0.953 | 1.035 | 0.176 |
| 0.30 | 0.972 | 0.948 | 1.052 | 0.210 |
| 0.50 | 0.969 | 0.951 | 1.070 | 0.233 |

## Findings

1. The envelope honestly covers the truth. Bound coverage is at or above nominal 95% across all heterogeneity regimes (96.9%-99.0%), never below the naive CI.
2. The bounds are informative, not trivially wide -- only 1.02x-1.07x the naive single-trial width. It achieves coverage by SHIFTING one bound toward the borrowed prior rather than ballooning.
3. The robust point estimate is well-behaved (RMSE 0.16-0.23 on log-effect scale), degrading gracefully as adjacent trials become a worse guide (rising tau).
4. Coverage is slightly conservative (above nominal) as the no-borrowing bound dominates -- acceptable for a "bounds you can trust" contract.

## Recommendation

ACCEPT. The k=1 partial-identification envelope does what it claims: bounds contain the true effect at >= the claimed rate while staying informative. No fabrication, no coverage failure observed. Non-blocking follow-up: extend the same known-truth coverage harness to adversarial_envelope and to missing_se_envelope on the effect scale.
