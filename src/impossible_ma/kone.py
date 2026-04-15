from dataclasses import dataclass
from typing import Literal
import numpy as np
from scipy import optimize

from .envelope import PossibilityEnvelope

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


def _posterior(y: float, se: float, mu_prior: float, se_prior: float) -> tuple[float, float]:
    v_y = se ** 2
    v_p = se_prior ** 2
    v_post = 1.0 / (1.0 / v_y + 1.0 / v_p)
    m_post = v_post * (y / v_y + mu_prior / v_p)
    return m_post, float(np.sqrt(v_post))


def _robust_posterior(
    y: float, se: float, mu_prior: float, se_prior: float, w: float
) -> tuple[float, float]:
    m_info, s_info = _posterior(y, se, mu_prior, se_prior)
    m_vague = y
    s_vague = se
    m = w * m_info + (1 - w) * m_vague
    s = float(
        np.sqrt(
            w * s_info ** 2
            + (1 - w) * s_vague ** 2
            + w * (1 - w) * (m_info - m_vague) ** 2
        )
    )
    return m, s


def _n_to_collapse(mu_se: float, target_se: float) -> int:
    return max(1, int(np.ceil(4.0 / (mu_se ** 2))))


def kone_envelope(inp: KoneInput) -> PossibilityEnvelope:
    fit = fit_map_prior(inp.adjacent)
    mu, tau, mu_se = fit["mu"], fit["tau"], fit["mu_se"]
    se_prior = float(np.sqrt(mu_se ** 2 + tau ** 2))

    m_vague, s_vague = inp.target_estimate, inp.target_se
    m_full, s_full = _posterior(inp.target_estimate, inp.target_se, mu, se_prior)
    m_robust, _s_robust = _robust_posterior(
        inp.target_estimate, inp.target_se, mu, se_prior, w=0.5
    )

    z = 1.959963984540054
    vague_ci = (m_vague - z * s_vague, m_vague + z * s_vague)
    full_ci = (m_full - z * s_full, m_full + z * s_full)

    lower = min(vague_ci[0], full_ci[0])
    upper = max(vague_ci[1], full_ci[1])

    n_needed = _n_to_collapse(mu_se, inp.target_se)

    return PossibilityEnvelope(
        lower=lower,
        upper=upper,
        point=m_robust,
        min_info=f"one additional trial with n >= {n_needed} in the same population",
        assumptions={
            "lower": "vague prior (MAP weight = 0)",
            "upper": "fully-informative prior (MAP weight = 1)",
            "point": "robust MAP mixture (weight = 0.5)",
        },
        case="k1",
        case_specific={
            "mu_prior": mu,
            "tau": tau,
            "mu_se": mu_se,
            "vague_ci": vague_ci,
            "full_borrowing_ci": full_ci,
            "robust_point": m_robust,
            "robust_se": _s_robust,
            "endpoint": inp.endpoint,
        },
    )
