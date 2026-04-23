from __future__ import annotations

import math
from typing import Any

import numpy as np
from scipy.stats import norm

from experiments._pool import reml_pool
from experiments.pilot_envelope import PilotEnvelope

_OR_TO_SMD = math.sqrt(3) / math.pi  # ~0.5513 (lessons.md: NOT sqrt(3/pi))
_VALID_FRAMES = ("continuous", "responder", "ordinal_probit")


def _continuous_to_smd(s: dict[str, Any]) -> tuple[float, float]:
    """Hedges' g with small-sample correction, variance via standard formula."""
    md = float(s["mean_diff"])
    sd = float(s["pooled_sd"])
    n1 = int(s["n1"])
    n2 = int(s["n2"])
    g = md / sd
    J = 1.0 - 3.0 / (4 * (n1 + n2) - 9)
    g *= J
    var = (n1 + n2) / (n1 * n2) + g ** 2 / (2 * (n1 + n2))
    return g, var


def _responder_to_smd(s: dict[str, Any]) -> tuple[float, float]:
    """Hasselblad-Hedges probit conversion with delta-method variance."""
    p1, p2 = float(s["p_ctrl"]), float(s["p_trt"])
    n1, n2 = int(s["n1"]), int(s["n2"])
    # clamp per lessons.md
    p1 = min(max(p1, 1e-10), 1 - 1e-10)
    p2 = min(max(p2, 1e-10), 1 - 1e-10)
    z1, z2 = norm.ppf(p1), norm.ppf(p2)
    smd = z2 - z1
    v1 = p1 * (1 - p1) / (n1 * norm.pdf(z1) ** 2)
    v2 = p2 * (1 - p2) / (n2 * norm.pdf(z2) ** 2)
    return smd, v1 + v2


def _ordinal_to_smd(s: dict[str, Any]) -> tuple[float, float]:
    """log-OR -> SMD via sqrt(3)/pi constant."""
    log_or = float(s["log_or"])
    se = float(s["se"])
    smd = log_or * _OR_TO_SMD
    var = (se * _OR_TO_SMD) ** 2
    return smd, var


def run(case: dict[str, Any]) -> PilotEnvelope:
    studies = case.get("studies")
    if studies is None:
        raise ValueError("case must contain 'studies'")
    cu = case.get("conversion_uncertainty", {}) or {}
    cont_cv = float(cu.get("continuous_sd_cv", 0.05))
    resp_cv = float(cu.get("responder_threshold_sd_cv", 0.10))
    defaults_used = []
    if "continuous_sd_cv" not in cu:
        defaults_used.append(f"continuous_sd_cv={cont_cv}")
    if "responder_threshold_sd_cv" not in cu:
        defaults_used.append(f"responder_threshold_sd_cv={resp_cv}")

    smds = []
    variances = []
    for s in studies:
        frame = s.get("frame")
        if frame not in _VALID_FRAMES:
            raise ValueError(
                f"frame must be one of {_VALID_FRAMES}, got {frame!r}"
            )
        if frame == "continuous":
            smd, var = _continuous_to_smd(s)
            var *= (1.0 + cont_cv) ** 2  # widen by conversion CV
        elif frame == "responder":
            smd, var = _responder_to_smd(s)
            var *= (1.0 + resp_cv) ** 2
        else:  # ordinal_probit
            smd, var = _ordinal_to_smd(s)
        smds.append(smd)
        variances.append(var)

    smds_arr = np.array(smds, dtype=float)
    vars_arr = np.array(variances, dtype=float)
    if len(smds_arr) < 2:
        raise ValueError("cross-framing pool requires k>=2")

    mu, se, tau2 = reml_pool(smds_arr, vars_arr)
    return PilotEnvelope(
        lower=mu - 1.96 * se,
        upper=mu + 1.96 * se,
        point=mu,
        min_info=(
            "pooled: converted SMDs via Hedges g / probit / log-OR*sqrt(3)/pi"
            + (f"; defaults {defaults_used}" if defaults_used else "")
        ),
        assumptions={
            "continuous_sd_cv": cont_cv,
            "responder_threshold_sd_cv": resp_cv,
            "defaults_used": defaults_used,
        },
        case=case.get("_case_name", "normal"),
        flavour="cross_framing",
        case_specific={"k": len(smds_arr), "tau2_reml": tau2},
    )
