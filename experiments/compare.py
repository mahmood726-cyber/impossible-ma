from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Callable

from experiments.cross_framing import run as run_cross_framing
from experiments.disconnected_nma import run as run_disconnected_nma
from experiments.era_collision import run as run_era_collision
from experiments.extreme_het import run as run_extreme_het
from experiments.pilot_envelope import PilotEnvelope

_FIXTURES_DIR = Path(__file__).parent / "fixtures"
_PILOTS: list[tuple[str, Callable[[dict], PilotEnvelope]]] = [
    ("disconnected_nma", run_disconnected_nma),
    ("extreme_het", run_extreme_het),
    ("cross_framing", run_cross_framing),
    ("era_collision", run_era_collision),
]


def _load(name: str) -> dict:
    return json.loads((_FIXTURES_DIR / f"{name}.json").read_text())


def _fmt(x: float | None) -> str:
    if x is None:
        return "—"
    if math.isinf(x):
        return "∞" if x > 0 else "-∞"
    return f"{x:.3f}"


def _truncate(s: str, n: int = 60) -> str:
    return s if len(s) <= n else s[: n - 1] + "…"


def run_all(output_path: Path) -> None:
    cases = {name: _load(name) for name, _ in _PILOTS}

    lines: list[str] = []
    lines.append("# Impossible Pooling Pilot — Comparison\n")
    lines.append("## Normal-case comparison\n")
    lines.append("| flavour | lower | upper | width | point | bounded? | min_info |")
    lines.append("|---|---|---|---|---|---|---|")
    for name, fn in _PILOTS:
        env = fn(cases[name]["normal"])
        width = env.upper - env.lower if math.isfinite(env.upper) and math.isfinite(env.lower) else math.inf
        bounded = "yes" if math.isfinite(env.upper) and math.isfinite(env.lower) else "no"
        lines.append(
            f"| {name} | {_fmt(env.lower)} | {_fmt(env.upper)} | {_fmt(width)} "
            f"| {_fmt(env.point)} | {bounded} | {_truncate(env.min_info)} |"
        )

    lines.append("\n## Degenerate-case behaviour\n")
    lines.append("| flavour | tight → classical? | unbounded flagged? | notes |")
    lines.append("|---|---|---|---|")
    for name, fn in _PILOTS:
        tight_ok = "—"
        unbounded_ok = "—"
        notes: list[str] = []
        try:
            env_t = fn(cases[name]["tight"])
            tight_ok = "yes" if env_t.point is not None or "classical" in env_t.min_info.lower() or "pooled" in env_t.min_info.lower() else "partial"
        except Exception as e:
            tight_ok = "error"
            notes.append(f"tight: {type(e).__name__}")
        try:
            env_u = fn(cases[name]["unbounded"])
            if math.isinf(env_u.upper) or math.isinf(env_u.lower):
                unbounded_ok = "inf-flagged"
            elif env_u.point is None and "refused" in env_u.min_info.lower():
                unbounded_ok = "refused"
            else:
                unbounded_ok = "bounded (wide)"
        except ValueError as e:
            unbounded_ok = "raises"
            notes.append(f"unbounded: {type(e).__name__}")
        lines.append(f"| {name} | {tight_ok} | {unbounded_ok} | {'; '.join(notes) or '—'} |")

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    run_all(_FIXTURES_DIR.parent / "comparison.md")
    print(f"wrote {_FIXTURES_DIR.parent / 'comparison.md'}")
