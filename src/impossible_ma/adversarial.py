"""Adversarial case: worst- and best-defensible pool across an inclusion-rule grid.

For each combination of publicly statable inclusion rules, apply the filter,
REML-pool with HKSJ CI (floor: max(1, Q/(k-1)) per advanced-stats.md), then
report the envelope of pooled estimates.
"""
from dataclasses import dataclass
from itertools import product
from typing import Iterator

import numpy as np
import pandas as pd
from scipy import optimize, stats as sstats

from .envelope import PossibilityEnvelope

MAX_POOLS = 1000


@dataclass(frozen=True)
class Rule:
    rob_cutoff: str
    n_floor: int
    followup_floor: int
    language: str
    pub_type: str

    def describe(self) -> str:
        return (
            f"ROB<={self.rob_cutoff}, n>={self.n_floor}, "
            f"followup>={self.followup_floor}mo, "
            f"lang={self.language}, type={self.pub_type}"
        )


def default_rule_grid() -> dict[str, list]:
    return {
        "rob_cutoff": ["low", "some", "moderate", "high", "any"],
        "n_floor": [0, 50, 200],
        "followup_floor": [0, 6, 12],
        "language": ["english_only", "any"],
        "pub_type": ["peer_reviewed_only", "any"],
    }


def enumerate_rules(grid: dict[str, list]) -> Iterator[Rule]:
    for rob, n, fu, lang, pub in product(
        grid["rob_cutoff"],
        grid["n_floor"],
        grid["followup_floor"],
        grid["language"],
        grid["pub_type"],
    ):
        yield Rule(
            rob_cutoff=rob,
            n_floor=n,
            followup_floor=fu,
            language=lang,
            pub_type=pub,
        )


_ROB_ORDER = {"low": 1, "some": 2, "moderate": 3, "high": 4, "any": 5}


def apply_rule(studies: pd.DataFrame, rule: Rule) -> pd.DataFrame:
    df = studies.copy()
    cutoff = _ROB_ORDER[rule.rob_cutoff]
    df = df[df["rob"].map(_ROB_ORDER) <= cutoff]
    df = df[df["n"] >= rule.n_floor]
    df = df[df["followup"] >= rule.followup_floor]
    if rule.language == "english_only":
        df = df[df["language"] == "english"]
    if rule.pub_type == "peer_reviewed_only":
        df = df[df["pub_type"] == "peer"]
    return df


def feasible_pools(
    studies: pd.DataFrame, rules: Iterator[Rule]
) -> Iterator[tuple[Rule, pd.DataFrame]]:
    count = 0
    for rule in rules:
        pool = apply_rule(studies, rule)
        if len(pool) < 3:
            continue
        yield rule, pool
        count += 1
        if count >= MAX_POOLS:
            return


def _reml_tau2(y: np.ndarray, v: np.ndarray) -> float:
    def neg_reml(log_tau2):
        tau2 = np.exp(log_tau2)
        w = 1.0 / (v + tau2)
        mu = np.sum(w * y) / np.sum(w)
        return -(
            -0.5
            * (
                np.sum(np.log(v + tau2))
                + np.sum(w * (y - mu) ** 2)
                + np.log(np.sum(w))
            )
        )

    res = optimize.minimize_scalar(neg_reml, bounds=(-20, 5), method="bounded")
    return float(np.exp(res.x))


def pool_reml_hksj(y, se) -> dict:
    y = np.asarray(y, dtype=float)
    se = np.asarray(se, dtype=float)
    k = len(y)
    if k < 2:
        raise ValueError("need k >= 2")
    v = se ** 2
    tau2 = _reml_tau2(y, v)
    w = 1.0 / (v + tau2)
    mu = float(np.sum(w * y) / np.sum(w))
    mu_fe = float(np.sum((1 / v) * y) / np.sum(1 / v))
    Q = float(np.sum((1 / v) * (y - mu_fe) ** 2))
    hksj_raw = np.sum(w * (y - mu) ** 2) / ((k - 1) * np.sum(w))
    floor = max(1.0, Q / (k - 1))
    hksj_floor_applied = hksj_raw < (floor / np.sum(w))
    hksj_var = max(hksj_raw, floor / np.sum(w))
    se_mu = float(np.sqrt(hksj_var))
    t_crit = float(sstats.t.ppf(0.975, df=k - 1))
    ci = (mu - t_crit * se_mu, mu + t_crit * se_mu)
    return {
        "estimate": mu,
        "se": se_mu,
        "ci_lower": float(ci[0]),
        "ci_upper": float(ci[1]),
        "tau2": tau2,
        "k": k,
        "Q": Q,
        "hksj_floor_applied": bool(hksj_floor_applied),
    }


def adversarial_envelope(
    studies: pd.DataFrame,
    grid: dict[str, list] | None = None,
) -> PossibilityEnvelope:
    grid = grid or default_rule_grid()
    pools = list(feasible_pools(studies, enumerate_rules(grid)))
    if not pools:
        raise ValueError("no feasible pool has k >= 3 under current grid")

    results: list[tuple[Rule, dict]] = []
    for rule, pool in pools:
        res = pool_reml_hksj(pool["estimate"].to_numpy(), pool["se"].to_numpy())
        results.append((rule, res))

    full_fit = pool_reml_hksj(
        studies["estimate"].to_numpy(), studies["se"].to_numpy()
    )

    sig = [
        (r, res) for r, res in results
        if res["ci_upper"] < 0 or res["ci_lower"] > 0
    ]
    if sig:
        lower_rule, lower_res = min(sig, key=lambda t: t[1]["estimate"])
        upper_rule, upper_res = max(sig, key=lambda t: t[1]["estimate"])
        no_sig = False
    else:
        lower_rule, lower_res = min(results, key=lambda t: t[1]["estimate"])
        upper_rule, upper_res = max(results, key=lambda t: t[1]["estimate"])
        no_sig = True
    lower, upper = lower_res["estimate"], upper_res["estimate"]

    # Widen envelope to contain the full-data REML (property test invariant).
    lower = min(lower, full_fit["estimate"])
    upper = max(upper, full_fit["estimate"])

    return PossibilityEnvelope(
        lower=float(lower),
        upper=float(upper),
        point=None,
        min_info="pre-registered inclusion protocol",
        assumptions={
            "lower_rule": lower_rule.describe(),
            "upper_rule": upper_rule.describe(),
            "significance_required": not no_sig,
        },
        case="adversarial",
        case_specific={
            "full_data_reml": full_fit,
            "n_pools": len(results),
            "no_significant_pool": no_sig,
            "lower_rule": lower_rule.describe(),
            "upper_rule": upper_rule.describe(),
            "audit_trail": [
                {"rule": r.describe(), **res} for r, res in results
            ],
        },
    )
