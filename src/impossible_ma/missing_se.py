"""Missing-SE reconstruction via four routes.

Route A: p-value -> SE via z = ppf(1 - p/2)
Route B: CI bounds -> SE via z or t(df)
Route C: test statistic -> SE; statistic treated as z by default, or t(df)
Route D: figure extraction (v1.1; raises NotImplementedError)
"""
import io
from dataclasses import dataclass, field
from statistics import median
from typing import Literal

import numpy as np
from PIL import Image, UnidentifiedImageError
from scipy import stats

from .envelope import PossibilityEnvelope


_MAX_IMAGE_BYTES = 10_000_000
_MIN_IMAGE_DIM = 100


def _decode_and_validate_image(image_bytes: bytes) -> np.ndarray:
    """Decode PNG/JPG bytes → grayscale uint8 numpy array (shape H, W).

    Raises ImageTooLargeError, UnsupportedFigureFormatError, ImageTooSmallError.
    """
    if len(image_bytes) > _MAX_IMAGE_BYTES:
        raise ImageTooLargeError(
            f"figure exceeds 10 MB ({len(image_bytes):,} bytes); "
            "compress or scale down before uploading"
        )
    try:
        img = Image.open(io.BytesIO(image_bytes))
        fmt = (img.format or "").upper()
    except UnidentifiedImageError as e:
        raise UnsupportedFigureFormatError(
            "could not decode image; only PNG or JPG is supported"
        ) from e
    if fmt not in ("PNG", "JPEG"):
        raise UnsupportedFigureFormatError(
            f"only PNG or JPG is supported; got {fmt or 'unknown'}"
        )
    w, h = img.size
    if w < _MIN_IMAGE_DIM or h < _MIN_IMAGE_DIM:
        raise ImageTooSmallError(
            f"figure is too small ({w}x{h}); re-export at 800px or larger"
        )
    return np.asarray(img.convert("L"), dtype=np.uint8)


def p_to_se(effect: float, p_value: float) -> float:
    if not (0.0 < p_value < 1.0):
        raise ValueError(f"p_value must be in (0, 1), got {p_value}")
    if effect == 0:
        raise ValueError("cannot reconstruct SE when effect is zero (z undefined)")
    z = stats.norm.ppf(1.0 - p_value / 2.0)
    return abs(effect) / z


def ci_to_se(
    ci_lower: float,
    ci_upper: float,
    conf_level: float = 0.95,
    df: int | None = None,
) -> float:
    if ci_lower >= ci_upper:
        raise ValueError(f"ci_lower ({ci_lower}) must be < ci_upper ({ci_upper})")
    if not (0.0 < conf_level < 1.0):
        raise ValueError(f"conf_level must be in (0, 1), got {conf_level}")
    alpha = 1.0 - conf_level
    if df is None:
        crit = stats.norm.ppf(1.0 - alpha / 2.0)
    else:
        crit = stats.t.ppf(1.0 - alpha / 2.0, df)
    return (ci_upper - ci_lower) / (2.0 * crit)


def stat_to_se(effect: float, statistic: float, df: int | None = None) -> float:
    if statistic == 0:
        raise ValueError("statistic cannot be zero")
    if effect == 0:
        raise ValueError("effect cannot be zero (ratio SE = effect/statistic undefined)")
    if df is None:
        z_equiv = abs(statistic)
    else:
        p = 2.0 * stats.t.sf(abs(statistic), df)
        z_equiv = stats.norm.ppf(1.0 - p / 2.0)
    return abs(effect) / z_equiv


def figure_to_se(image_path: str) -> float:
    """Route D (figure extraction) — deferred to v1.1."""
    raise NotImplementedError(
        "Route D (figure extraction) is scheduled for v1.1. "
        "For v1, supply SE via p-value (Route A), CI (Route B), or statistic (Route C)."
    )


# ---------- Route D exceptions ----------

class FigureExtractionError(ValueError):
    """Base class for all Route D (figure extraction) errors."""


class UnsupportedFigureFormatError(FigureExtractionError):
    """Image is not PNG or JPG, or PIL cannot decode it."""


class ImageTooSmallError(FigureExtractionError):
    """Image width or height is below the minimum for reliable extraction."""


class ImageTooLargeError(FigureExtractionError):
    """Image bytes exceed the maximum accepted size."""


class CalibrationError(FigureExtractionError):
    """Calibration clicks are invalid (coincident pixels, equal/negative values, out of bounds)."""


class ClickYOutOfBoundsError(FigureExtractionError):
    """Row-click y-coordinate falls outside the image."""


class NoWhiskerCapsDetectedError(FigureExtractionError):
    """Edge-detection found fewer than two peaks above threshold."""


class WhiskerCapsTooCloseError(FigureExtractionError):
    """Detected peaks span fewer than 10 pixels — likely a false positive."""


class HandlesCrossedError(FigureExtractionError):
    """Confirmed lower handle is not strictly left of the upper handle."""


class ConfidenceLevelInvalidError(FigureExtractionError):
    """conf_level must satisfy 0 < conf_level < 1."""


# ---------- Route D dataclasses ----------

@dataclass(frozen=True)
class Calibration:
    scale: Literal["log", "linear"]
    ref_pixel_1: int
    ref_value_1: float
    ref_pixel_2: int
    ref_value_2: float

    def __post_init__(self):
        if self.scale not in ("log", "linear"):
            raise CalibrationError(
                f"scale must be 'log' or 'linear', got {self.scale!r}"
            )
        if self.ref_pixel_1 == self.ref_pixel_2:
            raise CalibrationError(
                "calibration points must have distinct pixel x-positions"
            )
        if self.ref_value_1 == self.ref_value_2:
            raise CalibrationError(
                "calibration points must have distinct values"
            )
        if self.scale == "log":
            if self.ref_value_1 <= 0 or self.ref_value_2 <= 0:
                raise CalibrationError(
                    f"log scale requires positive values, got "
                    f"{self.ref_value_1} and {self.ref_value_2}"
                )


@dataclass(frozen=True)
class RowClick:
    click_y: int
    lower_handle_x: int
    upper_handle_x: int
    label: str | None = None


@dataclass(frozen=True)
class RowExtraction:
    effect: float
    se: float
    conf_level: float
    scale: Literal["log", "linear"]
    audit: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class FigureExtractionBundle:
    image_sha256: str
    calibration: Calibration
    rows: list[RowClick]
    conf_level: float
    results: list[RowExtraction]
    engine_version: str
    timestamp_iso: str


@dataclass
class MissingSeInput:
    effect: float
    p_value: float | None = None
    ci_lower: float | None = None
    ci_upper: float | None = None
    ci_conf_level: float = 0.95
    statistic: float | None = None
    df: int | None = None


def _routes(inp: MissingSeInput) -> dict[str, float]:
    out: dict[str, float] = {}
    if inp.p_value is not None:
        out["A_p_value"] = p_to_se(inp.effect, inp.p_value)
    if inp.ci_lower is not None and inp.ci_upper is not None:
        out["B_ci"] = ci_to_se(inp.ci_lower, inp.ci_upper, inp.ci_conf_level, inp.df)
    if inp.statistic is not None:
        out["C_statistic"] = stat_to_se(inp.effect, inp.statistic, inp.df)
    return out


def missing_se_envelope(inp: MissingSeInput) -> PossibilityEnvelope:
    routes = _routes(inp)
    if not routes:
        raise ValueError(
            "no SE route available: supply p_value, CI, or statistic"
        )

    se_values = list(routes.values())
    # Envelope is expressed on the SE scale (positive). Per PossibilityEnvelope
    # contract, lower <= upper numerically. Semantics (which bound is
    # conservative vs optimistic) live in `assumptions`.
    lower = min(se_values)
    upper = max(se_values)

    point: float | None = None
    if len(routes) >= 2:
        med = median(se_values)
        if all(abs(v - med) / med <= 0.10 for v in se_values):
            point = med
    if len(routes) == 1:
        point = se_values[0]  # lower == upper already

    return PossibilityEnvelope(
        lower=lower,
        upper=upper,
        point=point,
        min_info="raw SE from author correspondence",
        assumptions={
            "scale": "SE (positive); lower = narrowest reconstructed SE, upper = widest",
            "lower": "narrowest SE across successful routes (least conservative)",
            "upper": "widest SE across successful routes (most conservative)",
            "point": "median if >=2 routes agree within 10%, else None",
        },
        case="missing_se",
        case_specific={"routes": routes, "effect": inp.effect},
    )
