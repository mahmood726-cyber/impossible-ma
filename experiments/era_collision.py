from __future__ import annotations

import math
from typing import Any

import numpy as np

from experiments._pool import fe_pool
from experiments.pilot_envelope import PilotEnvelope


def run(case: dict[str, Any]) -> PilotEnvelope:
    studies = case.get("studies")
    if studies is None:
        raise ValueError("case must contain 'studies'")
    for s in studies:
        if "era" not in s:
            raise ValueError(f"study {s.get('id', '?')!r} missing 'era' label")

    bridging = case.get("bridging", {}) or {}
    beta_range = bridging.get("beta_range", [0.0, 0.0])
    beta_lo, beta_hi = float(beta_range[0]), float(beta_range[1])

    era1 = [s for s in studies if int(s["era"]) == 1]
    era2 = [s for s in studies if int(s["era"]) == 2]

    log_hrs = np.array([float(s["log_hr"]) for s in studies], dtype=float)
    ses = np.array([float(s["se"]) for s in studies], dtype=float)
    variances = ses ** 2

    # single-era case: bridging inapplicable, classical FE pool
    if len(era1) == 0 or len(era2) == 0:
        mu, se = fe_pool(log_hrs, variances)
        return PilotEnvelope(
            lower=mu - 1.96 * se,
            upper=mu + 1.96 * se,
            point=mu,
            min_info="single-era fixture: bridging inapplicable, classical FE pool",
            assumptions={"bridging_applied": False, "beta_range": [beta_lo, beta_hi]},
            case=case.get("_case_name", "tight"),
            flavour="era_collision",
            case_specific={"k_era1": len(era1), "k_era2": len(era2)},
        )

    era1_ref_rate = float(np.mean([float(s["control_rate_per_year"]) for s in era1]))
    era2_rate_ratios = np.array(
        [era1_ref_rate / float(s["control_rate_per_year"]) for s in era2],
        dtype=float,
    )

    grid = np.linspace(beta_lo, beta_hi, 21)
    lower = math.inf
    upper = -math.inf
    for beta in grid:
        adj = log_hrs.copy()
        for i, s in enumerate(studies):
            if int(s["era"]) == 2:
                j = era2.index(s)
                adj[i] = log_hrs[i] + beta * math.log(era2_rate_ratios[j])
        mu, se = fe_pool(adj, variances)
        lo_ci = mu - 1.96 * se
        hi_ci = mu + 1.96 * se
        if lo_ci < lower:
            lower = lo_ci
        if hi_ci > upper:
            upper = hi_ci

    point = None
    if beta_lo <= 0.0 <= beta_hi:
        # pool at beta=0 (unadjusted)
        mu0, _ = fe_pool(log_hrs, variances)
        point = mu0

    return PilotEnvelope(
        lower=float(lower),
        upper=float(upper),
        point=point,
        min_info=f"beta enumerated over [{beta_lo}, {beta_hi}] on 21-pt grid, FE pool",
        assumptions={
            "bridging_applied": True,
            "beta_range": [beta_lo, beta_hi],
            "era1_ref_rate": era1_ref_rate,
        },
        case=case.get("_case_name", "normal"),
        flavour="era_collision",
        case_specific={"k_era1": len(era1), "k_era2": len(era2), "grid_size": 21},
    )
