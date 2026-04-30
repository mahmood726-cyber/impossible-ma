from __future__ import annotations

import numpy as np
from scipy.optimize import minimize_scalar


def fe_pool(effects: np.ndarray, variances: np.ndarray) -> tuple[float, float]:
    """Inverse-variance fixed-effect pool. Returns (mu, se)."""
    effects = np.asarray(effects, dtype=float)
    variances = np.asarray(variances, dtype=float)
    if effects.shape != variances.shape or effects.ndim != 1:
        raise ValueError("effects and variances must be 1-D arrays of equal length")
    if np.any(variances <= 0):
        raise ValueError("variances must be strictly positive")
    weights = 1.0 / variances
    mu = float(np.sum(weights * effects) / np.sum(weights))
    se = float(1.0 / np.sqrt(np.sum(weights)))
    return mu, se


def reml_pool(
    effects: np.ndarray,
    variances: np.ndarray,
    tau2_max: float = 10.0,
) -> tuple[float, float, float]:
    """Random-effects REML pool via 1-D optimization. Returns (mu, se, tau2)."""
    effects = np.asarray(effects, dtype=float)
    variances = np.asarray(variances, dtype=float)
    if effects.shape != variances.shape or effects.ndim != 1:
        raise ValueError("effects and variances must be 1-D arrays of equal length")
    if np.any(variances <= 0):
        raise ValueError("variances must be strictly positive")
    if len(effects) < 2:
        raise ValueError(f"REML requires k>=2; got k={len(effects)}")

    def neg_reml_ll(tau2: float) -> float:
        if tau2 < 0:
            return np.inf
        weights = 1.0 / (variances + tau2)
        mu = np.sum(weights * effects) / np.sum(weights)
        log_likelihood = (
            -0.5 * np.sum(np.log(variances + tau2))
            - 0.5 * np.sum(weights * (effects - mu) ** 2)
            - 0.5 * np.log(np.sum(weights))
        )
        return -float(log_likelihood)

    result = minimize_scalar(neg_reml_ll, bounds=(0.0, tau2_max), method="bounded")
    tau2 = float(max(0.0, result.x))
    weights = 1.0 / (variances + tau2)
    mu = float(np.sum(weights * effects) / np.sum(weights))
    se = float(1.0 / np.sqrt(np.sum(weights)))
    return mu, se, tau2


def dl_tau2(effects: np.ndarray, variances: np.ndarray) -> float:
    """DerSimonian-Laird tau^2 (diagnostic use only). Returns tau2 >= 0."""
    effects = np.asarray(effects, dtype=float)
    variances = np.asarray(variances, dtype=float)
    k = len(effects)
    if k < 2:
        return 0.0
    weights = 1.0 / variances
    mu_fe = np.sum(weights * effects) / np.sum(weights)
    q_stat = np.sum(weights * (effects - mu_fe) ** 2)
    c_term = np.sum(weights) - np.sum(weights**2) / np.sum(weights)
    tau2 = (q_stat - (k - 1)) / c_term if c_term > 0 else 0.0
    return float(max(0.0, tau2))
