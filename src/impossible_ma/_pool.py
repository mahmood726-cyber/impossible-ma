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
    w = 1.0 / variances
    mu = float(np.sum(w * effects) / np.sum(w))
    se = float(1.0 / np.sqrt(np.sum(w)))
    return mu, se


def reml_pool(
    effects: np.ndarray, variances: np.ndarray, tau2_max: float = 10.0
) -> tuple[float, float, float]:
    """Random-effects REML pool via 1-D optimization. Returns (mu, se, tau2)."""
    effects = np.asarray(effects, dtype=float)
    variances = np.asarray(variances, dtype=float)
    if effects.shape != variances.shape or effects.ndim != 1:
        raise ValueError("effects and variances must be 1-D arrays of equal length")
    if np.any(variances <= 0):
        raise ValueError("variances must be strictly positive")
    k = len(effects)
    if k < 2:
        raise ValueError("REML requires k>=2; got k=" + str(k))

    def neg_reml_ll(tau2: float) -> float:
        if tau2 < 0:
            return np.inf
        w = 1.0 / (variances + tau2)
        mu = np.sum(w * effects) / np.sum(w)
        ll = (
            -0.5 * np.sum(np.log(variances + tau2))
            - 0.5 * np.sum(w * (effects - mu) ** 2)
            - 0.5 * np.log(np.sum(w))
        )
        return -ll

    res = minimize_scalar(neg_reml_ll, bounds=(0.0, tau2_max), method="bounded")
    tau2 = float(max(0.0, res.x))
    w = 1.0 / (variances + tau2)
    mu = float(np.sum(w * effects) / np.sum(w))
    se = float(1.0 / np.sqrt(np.sum(w)))
    return mu, se, tau2


def dl_tau2(effects: np.ndarray, variances: np.ndarray) -> float:
    """DerSimonian-Laird tau^2 (diagnostic use only). Returns tau2 >= 0."""
    effects = np.asarray(effects, dtype=float)
    variances = np.asarray(variances, dtype=float)
    k = len(effects)
    if k < 2:
        return 0.0
    w = 1.0 / variances
    mu_fe = np.sum(w * effects) / np.sum(w)
    Q = np.sum(w * (effects - mu_fe) ** 2)
    c = np.sum(w) - np.sum(w ** 2) / np.sum(w)
    tau2 = (Q - (k - 1)) / c if c > 0 else 0.0
    return float(max(0.0, tau2))
