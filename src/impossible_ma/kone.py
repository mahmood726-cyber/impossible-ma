from dataclasses import dataclass
from typing import Literal
import numpy as np
from scipy import optimize

Endpoint = Literal["binary", "continuous", "tte"]
_VALID_ENDPOINTS = ("binary", "continuous", "tte")


@dataclass
class KoneInput:
    target_estimate: float
    target_se: float
    adjacent: list[tuple[float, float]]
    endpoint: Endpoint

    def __post_init__(self):
        if self.endpoint not in _VALID_ENDPOINTS:
            raise ValueError(
                f"endpoint must be one of {_VALID_ENDPOINTS}, got {self.endpoint!r}"
            )
        if self.target_se <= 0:
            raise ValueError("target_se must be positive")
        if len(self.adjacent) < 3:
            raise ValueError(
                f"need at least 3 adjacent trials, got {len(self.adjacent)}"
            )


def fit_map_prior(adjacent: list[tuple[float, float]]) -> dict[str, float]:
    if len(adjacent) < 3:
        raise ValueError(f"need at least 3 adjacent trials, got {len(adjacent)}")

    y = np.array([e for e, _ in adjacent], dtype=float)
    se = np.array([s for _, s in adjacent], dtype=float)
    v = se ** 2

    def neg_reml(log_tau2):
        tau2 = np.exp(log_tau2)
        w = 1.0 / (v + tau2)
        mu_hat = np.sum(w * y) / np.sum(w)
        resid = y - mu_hat
        ll = -0.5 * (
            np.sum(np.log(v + tau2))
            + np.sum(w * resid ** 2)
            + np.log(np.sum(w))
        )
        return -ll

    res = optimize.minimize_scalar(neg_reml, bounds=(-20, 5), method="bounded")
    tau2 = float(np.exp(res.x))
    w = 1.0 / (v + tau2)
    mu = float(np.sum(w * y) / np.sum(w))
    mu_se = float(np.sqrt(1.0 / np.sum(w)))
    return {"mu": mu, "tau": float(np.sqrt(tau2)), "mu_se": mu_se}
