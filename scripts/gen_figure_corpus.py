"""Generate the Route D test-fixture corpus.

Produces ~20 horizontal forest plots via matplotlib with known (effect, SE)
per study, plus a per-fixture truth.json carrying the calibration points
and ground-truth pixel positions.

Usage:
    python scripts/gen_figure_corpus.py [--out tests/fixtures/figure_corpus/]
"""
from __future__ import annotations

import argparse
import io
import json
import math
from dataclasses import dataclass, asdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


@dataclass
class FixtureSpec:
    slug: str
    scale: str           # "log" or "linear"
    axis_min: float
    axis_max: float
    width_px: int
    height_px: int
    fmt: str             # "png", "jpg"
    jpg_quality: int | None
    n_studies: int
    marker: str          # "s" (square) or "o" (circle)
    effects: list[float]  # native-scale truth values
    ses: list[float]      # native-scale truth SE


def _fixtures() -> list[FixtureSpec]:
    """Fixed parameter set - 20 fixtures total. Seeded for reproducibility."""
    rng = np.random.default_rng(20260418)
    specs: list[FixtureSpec] = []

    def eff_log(n):
        return rng.uniform(-1.2, 1.2, size=n).tolist()

    def eff_linear(n):
        return rng.uniform(-0.6, 0.6, size=n).tolist()

    def ses_for(n):
        return rng.uniform(0.08, 0.35, size=n).tolist()

    configs = [
        # (slug, scale, min, max, w, h, fmt, q, n_studies, marker)
        ("log_narrow_sq_400_png",   "log",    0.3,  3.0,  400,  300, "png", None, 5,  "s"),
        ("log_narrow_sq_800_png",   "log",    0.3,  3.0,  800,  600, "png", None, 7,  "s"),
        ("log_narrow_sq_1600_png",  "log",    0.3,  3.0, 1600, 1200, "png", None, 9,  "s"),
        ("log_narrow_sq_800_jpg70", "log",    0.3,  3.0,  800,  600, "jpg",   70, 7,  "s"),
        ("log_wide_sq_800_png",     "log",    0.05, 20.0, 800,  600, "png", None, 8,  "s"),
        ("log_wide_sq_1600_png",    "log",    0.05, 20.0,1600, 1200, "png", None, 10, "s"),
        ("log_wide_sq_800_jpg85",   "log",    0.05, 20.0, 800,  600, "jpg",   85, 8,  "s"),
        ("log_wide_sq_800_jpg95",   "log",    0.05, 20.0, 800,  600, "jpg",   95, 8,  "s"),
        ("lin_narrow_sq_400_png",   "linear", -0.5, 0.5,  400,  300, "png", None, 5,  "s"),
        ("lin_narrow_sq_800_png",   "linear", -0.5, 0.5,  800,  600, "png", None, 7,  "s"),
        ("lin_narrow_sq_1600_png",  "linear", -0.5, 0.5, 1600, 1200, "png", None, 9,  "s"),
        ("lin_narrow_sq_800_jpg70", "linear", -0.5, 0.5,  800,  600, "jpg",   70, 7,  "s"),
        ("lin_wide_sq_800_png",     "linear", -3.0, 3.0,  800,  600, "png", None, 8,  "s"),
        ("lin_wide_sq_1600_png",    "linear", -3.0, 3.0, 1600, 1200, "png", None, 10, "s"),
        ("lin_wide_sq_800_jpg85",   "linear", -3.0, 3.0,  800,  600, "jpg",   85, 8,  "s"),
        ("log_narrow_circle_800",   "log",    0.3,  3.0,  800,  600, "png", None, 6,  "o"),
        ("log_wide_circle_800",     "log",    0.05, 20.0, 800,  600, "png", None, 7,  "o"),
        ("log_narrow_15studies",    "log",    0.3,  3.0,  800,  900, "png", None, 15, "s"),
        ("lin_narrow_circle_800",   "linear", -0.5, 0.5,  800,  600, "png", None, 6,  "o"),
        ("log_wide_5studies_tight", "log",    0.1,  10.0, 800,  600, "png", None, 5,  "s"),
    ]
    for cfg in configs:
        slug, scale, amin, amax, w, h, fmt, q, n, marker = cfg
        effects = eff_log(n) if scale == "log" else eff_linear(n)
        ses = ses_for(n)
        specs.append(FixtureSpec(
            slug=slug, scale=scale, axis_min=amin, axis_max=amax,
            width_px=w, height_px=h, fmt=fmt, jpg_quality=q,
            n_studies=n, marker=marker, effects=effects, ses=ses,
        ))
    return specs


def _render(spec: FixtureSpec) -> tuple[bytes, dict]:
    """Render one fixture. Returns (image_bytes, truth_dict)."""
    z = 1.959964  # 95%
    fig, ax = plt.subplots(figsize=(spec.width_px / 100, spec.height_px / 100),
                           dpi=100)
    y_positions = list(range(spec.n_studies, 0, -1))
    lower = [e - z * s for e, s in zip(spec.effects, spec.ses)]
    upper = [e + z * s for e, s in zip(spec.effects, spec.ses)]

    if spec.scale == "log":
        display_effects = [math.exp(e) for e in spec.effects]
        display_lower = [math.exp(l) for l in lower]
        display_upper = [math.exp(u) for u in upper]
        ax.set_xscale("log")
        ax.set_xlim(spec.axis_min, spec.axis_max)
    else:
        display_effects = spec.effects
        display_lower = lower
        display_upper = upper
        ax.set_xlim(spec.axis_min, spec.axis_max)

    for y, eff, lo, hi in zip(y_positions, display_effects,
                               display_lower, display_upper):
        ax.plot([lo, hi], [y, y], color="black", linewidth=1.2)
        cap_h = 0.25
        ax.plot([lo, lo], [y - cap_h, y + cap_h], color="black", linewidth=1.2)
        ax.plot([hi, hi], [y - cap_h, y + cap_h], color="black", linewidth=1.2)
        ax.plot(eff, y, marker=spec.marker, color="black", markersize=6)

    ax.set_yticks(y_positions)
    ax.set_yticklabels([f"Study {i}" for i in range(1, spec.n_studies + 1)])
    ax.axvline(1.0 if spec.scale == "log" else 0.0, color="gray",
               linestyle="--", linewidth=0.8)
    fig.tight_layout()

    buf = io.BytesIO()
    if spec.fmt == "png":
        fig.savefig(buf, format="png", dpi=100)
    else:
        fig.savefig(buf, format="jpeg", dpi=100,
                    pil_kwargs={"quality": spec.jpg_quality})
    image_bytes = buf.getvalue()

    # Derive ground-truth pixel positions via ax.transData.
    # matplotlib display coords: y-axis points UP (bottom-left origin).
    # Numpy image array: y-axis points DOWN (top-left origin).
    # Flip y: click_y_px = height_px - display_y_px.
    fig.canvas.draw()
    true_rows = []
    for i, (y, eff, lo, hi) in enumerate(zip(
        y_positions, spec.effects, lower, upper,
    )):
        disp_eff_x = (
            ax.transData.transform((math.exp(eff) if spec.scale == "log" else eff, y))[0]
        )
        disp_lo_x = ax.transData.transform(
            (math.exp(lo) if spec.scale == "log" else lo, y)
        )[0]
        disp_hi_x = ax.transData.transform(
            (math.exp(hi) if spec.scale == "log" else hi, y)
        )[0]
        disp_y = ax.transData.transform((1.0, y))[1]
        click_y_px = int(round(spec.height_px - disp_y))
        true_rows.append({
            "study_index": i,
            "label": f"Study {i + 1}",
            "click_y": click_y_px,
            "lower_x_true": int(round(disp_lo_x)),
            "upper_x_true": int(round(disp_hi_x)),
            "effect_x_true": int(round(disp_eff_x)),
            "effect_true": float(spec.effects[i]),
            "se_true": float(spec.ses[i]),
        })

    # Calibration ground-truth: two tick values inside the axis range.
    if spec.scale == "log":
        cal_v1 = spec.axis_min * 1.5
        cal_v2 = spec.axis_max / 1.5
    else:
        cal_v1 = spec.axis_min + (spec.axis_max - spec.axis_min) * 0.2
        cal_v2 = spec.axis_min + (spec.axis_max - spec.axis_min) * 0.8
    cal_p1 = int(round(ax.transData.transform((cal_v1, 1.0))[0]))
    cal_p2 = int(round(ax.transData.transform((cal_v2, 1.0))[0]))

    plt.close(fig)

    truth = {
        "slug": spec.slug,
        "scale": spec.scale,
        "axis_min": spec.axis_min,
        "axis_max": spec.axis_max,
        "width_px": spec.width_px,
        "height_px": spec.height_px,
        "format": spec.fmt,
        "jpg_quality": spec.jpg_quality,
        "n_studies": spec.n_studies,
        "marker": spec.marker,
        "calibration_clicks": [
            {"pixel_x": cal_p1, "value": cal_v1},
            {"pixel_x": cal_p2, "value": cal_v2},
        ],
        "studies": true_rows,
        "conf_level": 0.95,
    }
    return image_bytes, truth


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path,
                    default=Path("tests/fixtures/figure_corpus"))
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    specs = _fixtures()
    for spec in specs:
        img_bytes, truth = _render(spec)
        ext = "png" if spec.fmt == "png" else "jpg"
        (args.out / f"{spec.slug}.{ext}").write_bytes(img_bytes)
        (args.out / f"{spec.slug}.truth.json").write_text(
            json.dumps(truth, indent=2), encoding="utf-8"
        )
        print(f"[fixture] {spec.slug} ({len(img_bytes):,} bytes)")
    print(f"[done] {len(specs)} fixtures in {args.out}")


if __name__ == "__main__":
    main()
