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
    except Image.DecompressionBombError as e:
        raise ImageTooLargeError(
            "figure dimensions exceed Pillow's decompression bomb threshold; "
            "scale down to a reasonable resolution before uploading"
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
    try:
        return np.asarray(img.convert("L"), dtype=np.uint8)
    except OSError as e:
        raise UnsupportedFigureFormatError(
            "could not decode image; file appears truncated or corrupted"
        ) from e


_DEFAULT_BAND_HEIGHT = 7
_MIN_CAP_SEPARATION = 10
_THRESHOLD_MAD_MULTIPLIER = 3.0
_MIN_THRESHOLD_FLOOR = 0.02
# Peak-collapse window: a single vertical cap produces centred-gradient peaks
# 2 px apart (columns c-1 and c+1 around the cap at column c). Using
# min_sep=3 collapses those intra-cap duplicates while preserving legitimately
# close cap pairs so WhiskerCapsTooCloseError can fire on span < 10 px.
_PEAK_MIN_SEPARATION = 3


def _column_gradient_signal(band: np.ndarray) -> np.ndarray:
    """Centred horizontal gradient |I[:, x+1] - I[:, x-1]| summed over rows,
    normalised to [0, 1]. Vertical edges produce tall peaks; horizontal bars
    have weak gradient along their length."""
    grad = np.abs(
        band[:, 2:].astype(np.int16) - band[:, :-2].astype(np.int16)
    )  # shape: (band_h, W-2); per-row bound is 255 for uint8
    col_sum = grad.sum(axis=0)  # shape: (W-2,); per-column bound is band_h * 255
    padded = np.zeros(band.shape[1], dtype=np.float64)
    padded[1:-1] = col_sum
    return padded / (band.shape[0] * 255.0)


def _find_peaks(
    signal: np.ndarray, threshold: float, min_sep: int
) -> list[int]:
    """Return column indices of above-threshold peaks with min-separation
    enforced greedily from left to right (retains the larger peak inside
    any colliding cluster)."""
    above = np.where(signal > threshold)[0]
    if len(above) == 0:
        return []
    peaks: list[int] = []
    for x in above:
        if not peaks or (x - peaks[-1]) >= min_sep:
            peaks.append(int(x))
        else:
            # Keep whichever is larger
            if signal[x] > signal[peaks[-1]]:
                peaks[-1] = int(x)
    return peaks


def propose_whisker_caps(
    image_bytes: bytes,
    click_y: int,
    band_height: int = _DEFAULT_BAND_HEIGHT,
) -> tuple[int, int]:
    """Propose whisker-cap x-positions in a horizontal band centred on
    click_y. The result is a proposal, not authoritative — users are
    expected to confirm or drag-correct the returned positions.

    Algorithm: centred horizontal gradient summed over a ``band_height``
    band, thresholded at ``median + 3*MAD`` (floor ``_MIN_THRESHOLD_FLOOR``),
    with near-neighbour peak collapse to suppress intra-edge gradient echoes.
    Returns the leftmost and rightmost surviving peaks as (lower_x, upper_x).

    Limitations
    -----------
    The leftmost/rightmost policy assumes the whisker caps are the outermost
    gradient features in the band. Random-effects summary diamonds commonly
    extend further than per-study whisker caps, so **clicking on a summary
    row will return the diamond's extent**, not the summary's
    whisker-equivalent width. Recommend clicking on per-study rows only.
    Similarly, anything drawn past the caps in the band y-range (annotation
    arrows, connector lines) will pollute the proposal.

    Parameters
    ----------
    image_bytes : bytes
        PNG or JPG image bytes.
    click_y : int
        Pixel y-coordinate of the row to extract. Must be within image
        height.
    band_height : int, default 7
        Height in pixels of the horizontal band to scan. Must be >= 1.

    Raises
    ------
    ValueError
        If band_height < 1.
    ClickYOutOfBoundsError
        If click_y is outside the image.
    NoWhiskerCapsDetectedError
        If fewer than 2 above-threshold peaks are found.
    WhiskerCapsTooCloseError
        If the surviving peaks span fewer than 10 pixels.
    UnsupportedFigureFormatError, ImageTooSmallError, ImageTooLargeError
        From the image-decode gate.
    """
    if band_height < 1:
        raise ValueError(
            f"band_height must be >= 1, got {band_height}"
        )
    arr = _decode_and_validate_image(image_bytes)
    h, w = arr.shape
    if click_y < 0 or click_y >= h:
        raise ClickYOutOfBoundsError(
            f"click_y={click_y} is outside image height {h}"
        )
    half = band_height // 2
    y_lo = max(0, click_y - half)
    y_hi = min(h, click_y + half + 1)
    band = arr[y_lo:y_hi, :]
    signal = _column_gradient_signal(band)
    med = float(np.median(signal))
    mad = float(np.median(np.abs(signal - med)))
    threshold = max(med + _THRESHOLD_MAD_MULTIPLIER * mad, _MIN_THRESHOLD_FLOOR)
    peaks = _find_peaks(signal, threshold, min_sep=_PEAK_MIN_SEPARATION)
    if len(peaks) < 2:
        raise NoWhiskerCapsDetectedError(
            f"found {len(peaks)} peak(s) above threshold {threshold:.4f} "
            f"(median={med:.4f}, MAD={mad:.4f}); detection did not converge"
        )
    lo, hi = peaks[0], peaks[-1]
    if hi - lo < _MIN_CAP_SEPARATION:
        raise WhiskerCapsTooCloseError(
            f"detected peaks span {hi - lo} px (< {_MIN_CAP_SEPARATION}); "
            "likely false positive on a marker or noise"
        )
    return lo, hi


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
