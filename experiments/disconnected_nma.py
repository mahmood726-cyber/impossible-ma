from __future__ import annotations

import math
from typing import Any

import numpy as np

from experiments._pool import fe_pool
from experiments.pilot_envelope import PilotEnvelope


def _pool_bubble(bubble: dict[str, Any]) -> tuple[float, float]:
    """Return (d_hat, var) for one bubble. k=1 uses the study directly."""
    studies = bubble.get("studies")
    if studies is None or len(studies) == 0:
        raise ValueError("bubble has no studies (k=0)")
    effects = np.array([s["effect"] for s in studies], dtype=float)
    ses = np.array([s["se"] for s in studies], dtype=float)
    variances = ses ** 2
    if len(studies) == 1:
        return float(effects[0]), float(variances[0])
    mu, se = fe_pool(effects, variances)
    return mu, se ** 2


def run(case: dict[str, Any]) -> PilotEnvelope:
    b1 = case.get("bubble_1")
    b2 = case.get("bubble_2")
    bridging = case.get("bridging", {})
    if b1 is None or b2 is None:
        raise ValueError("case must contain 'bubble_1' and 'bubble_2'")

    d1, v1 = _pool_bubble(b1)
    d2, v2 = _pool_bubble(b2)

    delta_raw = bridging.get("delta_log_odds")
    if delta_raw is None:
        delta = math.inf
    else:
        delta = float(delta_raw)

    base_center = d1 - d2
    base_se = math.sqrt(v1 + v2)

    if math.isinf(delta):
        return PilotEnvelope(
            lower=-math.inf,
            upper=math.inf,
            point=None,
            min_info="unbounded: bridging delta_log_odds unconstrained",
            assumptions={"delta_log_odds": None, "bubble_1_d": d1, "bubble_2_d": d2},
            case="unbounded",
            flavour="disconnected_nma",
            case_specific={"base_center": base_center, "base_se": base_se},
        )

    grid = np.linspace(-delta, +delta, 21)
    lowers = base_center + grid - 1.96 * base_se
    uppers = base_center + grid + 1.96 * base_se
    lower = float(np.min(lowers))
    upper = float(np.max(uppers))

    point = float(base_center) if delta == 0.0 else None
    min_info = (
        f"delta_log_odds={delta}, bubble_pool=FE, grid=21"
        if delta > 0
        else f"delta_log_odds=0 (classical indirect), bubble_pool=FE"
    )

    return PilotEnvelope(
        lower=lower,
        upper=upper,
        point=point,
        min_info=min_info,
        assumptions={"delta_log_odds": delta, "bubble_1_d": d1, "bubble_2_d": d2},
        case=case.get("_case_name", "normal"),
        flavour="disconnected_nma",
        case_specific={"grid_size": 21, "base_se": base_se},
    )
