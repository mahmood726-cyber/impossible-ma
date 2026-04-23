from __future__ import annotations

from typing import Any

import numpy as np

from experiments._pool import dl_tau2, fe_pool, reml_pool
from experiments.pilot_envelope import PilotEnvelope


def run(case: dict[str, Any]) -> PilotEnvelope:
    studies = case.get("studies")
    if studies is None:
        raise ValueError("case must contain 'studies'")
    k = len(studies)
    if k < 3:
        raise ValueError(
            f"k={k} too small; use impossible_ma.kone for k=1, collect more studies otherwise"
        )

    thresholds = case.get("thresholds", {})
    i2_threshold = float(thresholds.get("i2_refuse_point", 0.80))
    tau_ratio_threshold = float(thresholds.get("tau_ratio_refuse", 2.0))

    effects = np.array([s["effect"] for s in studies], dtype=float)
    ses = np.array([s["se"] for s in studies], dtype=float)
    variances = ses ** 2

    # FE baseline for I^2 and tau ratio diagnostic
    mu_fe, se_fe = fe_pool(effects, variances)
    tau2_dl = dl_tau2(effects, variances)
    w = 1.0 / variances
    Q = float(np.sum(w * (effects - mu_fe) ** 2))
    df = k - 1
    i2 = max(0.0, (Q - df) / Q) if Q > 0 else 0.0
    tau_ratio = (np.sqrt(tau2_dl) / abs(mu_fe)) if mu_fe != 0 else float("inf")

    refuse = (i2 >= i2_threshold) or (tau_ratio >= tau_ratio_threshold)

    if refuse:
        lower = float(np.min(effects - 1.96 * ses))
        upper = float(np.max(effects + 1.96 * ses))
        return PilotEnvelope(
            lower=lower,
            upper=upper,
            point=None,
            min_info=f"refused: I2={i2:.2f}, tau_ratio={tau_ratio:.2f}, study-level envelope",
            assumptions={
                "i2_refuse_point": i2_threshold,
                "tau_ratio_refuse": tau_ratio_threshold,
                "i2_observed": i2,
                "tau_ratio_observed": tau_ratio,
            },
            case=case.get("_case_name", "normal"),
            flavour="extreme_het",
            case_specific={"k": k, "Q": Q, "tau2_dl": tau2_dl},
        )

    mu, se, tau2_reml = reml_pool(effects, variances)
    return PilotEnvelope(
        lower=mu - 1.96 * se,
        upper=mu + 1.96 * se,
        point=mu,
        min_info=f"pooled: I2={i2:.2f} below refusal threshold, REML",
        assumptions={
            "i2_refuse_point": i2_threshold,
            "tau_ratio_refuse": tau_ratio_threshold,
            "i2_observed": i2,
            "tau_ratio_observed": tau_ratio,
        },
        case=case.get("_case_name", "tight"),
        flavour="extreme_het",
        case_specific={"k": k, "tau2_reml": tau2_reml},
    )
