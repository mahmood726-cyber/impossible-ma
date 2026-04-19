"""Missing-SE reconstruction via four routes.

Route A: p-value -> SE via z = ppf(1 - p/2)
Route B: CI bounds -> SE via z or t(df)
Route C: test statistic -> SE; statistic treated as z by default, or t(df)
Route D: figure extraction — extract_se_from_figure() from confirmed
         whisker-cap handle positions on a horizontal forest plot.
"""
import hashlib
import io
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
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


def _choose_bg_offsets(
    click_y: int, h: int, band_height: int
) -> list[int]:
    """Return up to 3 reference-band y-offsets far from click_y for
    background-gradient sampling. The offsets are spaced by ~1/4 of the
    image height so they land between typical study rows (which are
    evenly spaced on a forest plot). If the image is too short to fit
    separated reference bands, returns fewer (may return empty list —
    caller skips background subtraction)."""
    min_sep = 3 * band_height  # at least 3× band-height away from click_y
    candidates = [h // 4, h // 2, 3 * h // 4]
    picks: list[int] = []
    for c in candidates:
        if abs(c - click_y) >= min_sep and 0 <= c < h:
            # Avoid duplicates
            if not any(abs(c - p) < band_height for p in picks):
                picks.append(c)
    return picks


def propose_whisker_caps(
    image_bytes: bytes,
    click_y: int,
    band_height: int = _DEFAULT_BAND_HEIGHT,
    search_x_range: tuple[int, int] | None = None,
) -> tuple[int, int]:
    """Propose whisker-cap x-positions in a horizontal band centred on
    click_y. The result is a proposal, not authoritative — users are
    expected to confirm or drag-correct the returned positions.

    Algorithm: centred horizontal gradient summed over a ``band_height``
    band, minus a background gradient sampled at up to 3 reference bands
    far from click_y (suppresses full-height vertical lines like
    null-effect axvlines, axis spines, and gridlines; row-local whisker
    caps survive because they produce no signal in the reference bands).
    Thresholded at ``median + 3*MAD`` (floor ``_MIN_THRESHOLD_FLOOR``),
    with near-neighbour peak collapse to suppress intra-edge gradient
    echoes. Returns the leftmost and rightmost surviving peaks as
    (lower_x, upper_x).

    Limitations
    -----------
    The leftmost/rightmost policy assumes the whisker caps are the outermost
    gradient features in the band. Random-effects summary diamonds commonly
    extend further than per-study whisker caps, so **clicking on a summary
    row will return the diamond's extent**, not the summary's
    whisker-equivalent width. Recommend clicking on per-study rows only.
    Similarly, anything drawn past the caps in the band y-range (annotation
    arrows, connector lines) will pollute the proposal.

    Additionally, dashed vertical lines that span the plot height (e.g.
    null-effect reference lines at HR=1 or SMD=0) are only partially
    suppressed by background subtraction because the dash pattern varies
    across y-bands. Expect to drag-correct on any row whose real cap
    falls near such a reference line. v0.1.1 ships validated against a
    corpus of clean horizontal forest plots without null lines —
    production plots should still work for most rows, with the
    user-in-the-loop drag-correct flow covering the rest.

    Parameters
    ----------
    image_bytes : bytes
        PNG or JPG image bytes.
    click_y : int
        Pixel y-coordinate of the row to extract. Must be within image
        height.
    band_height : int, default 7
        Height in pixels of the horizontal band to scan. Must be >= 1.
    search_x_range : tuple[int, int], optional
        If given, restricts peak search to columns ``x_lo..x_hi`` inclusive.
        Use the calibration bbox to exclude gutter features (y-axis tick
        labels, margin text) that would otherwise win as leftmost/rightmost
        peaks. Must satisfy ``0 <= x_lo < x_hi < width``.

    Raises
    ------
    ValueError
        If band_height < 1, or if search_x_range is invalid.
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
    if search_x_range is not None:
        x_lo, x_hi = search_x_range
        if not (0 <= x_lo < x_hi < w):
            raise ValueError(
                f"search_x_range={search_x_range} invalid; must satisfy "
                f"0 <= x_lo < x_hi < width ({w})"
            )
    half = band_height // 2
    y_lo = max(0, click_y - half)
    y_hi = min(h, click_y + half + 1)
    band = arr[y_lo:y_hi, :]
    signal = _column_gradient_signal(band)

    # Background subtraction: suppress vertical lines that span the full
    # plot height (null-effect axvline, axis spines, gridlines). These
    # produce equal signal at the clicked band AND at a reference band
    # far from any whisker row; whisker caps only appear in their own
    # row's band. We sample THREE reference bands at different y
    # offsets to avoid picking a reference that happens to coincide
    # with another study's whiskers, and take the MINIMUM of the three
    # as the background estimate (so a real cap's reference-band
    # signal is ~0, but an axvline's is ~the peak value).
    bg_y_offsets = _choose_bg_offsets(click_y, h, band_height)
    if bg_y_offsets:
        bg_signals = []
        for by in bg_y_offsets:
            b_lo = max(0, by - half)
            b_hi = min(h, by + half + 1)
            bg_band = arr[b_lo:b_hi, :]
            # Match row count to the click band so the normalisation is
            # comparable (if the clicked band was clipped by the image
            # edge). If the bg band has different row count, truncate
            # it to match.
            min_rows = min(bg_band.shape[0], band.shape[0])
            bg_signals.append(_column_gradient_signal(bg_band[:min_rows, :]))
        # Minimum across the 3 bg bands per column
        bg = np.min(np.stack(bg_signals, axis=0), axis=0)
        signal = np.maximum(signal - bg, 0.0)

    # Mask columns outside the search range so gutter/margin gradients
    # (tick labels, axis text) cannot win as leftmost/rightmost.
    if search_x_range is not None:
        signal[: search_x_range[0]] = 0.0
        signal[search_x_range[1] + 1:] = 0.0

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
        if not (math.isfinite(self.ref_value_1) and math.isfinite(self.ref_value_2)):
            raise CalibrationError(
                f"calibration values must be finite, got "
                f"ref_value_1={self.ref_value_1}, ref_value_2={self.ref_value_2}"
            )
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


def _calibration_params(cal: Calibration) -> tuple[float, float]:
    """Return (m, b) such that the native-scale value at pixel x is m*x + b.
    For log scale, 'value' means log(hr)."""
    if cal.scale == "log":
        v1, v2 = math.log(cal.ref_value_1), math.log(cal.ref_value_2)
    else:
        v1, v2 = cal.ref_value_1, cal.ref_value_2
    m = (v2 - v1) / (cal.ref_pixel_2 - cal.ref_pixel_1)
    b = v1 - m * cal.ref_pixel_1
    return m, b


def extract_se_from_figure(
    image_bytes: bytes,
    calibration: Calibration,
    rows: list[RowClick],
    conf_level: float = 0.95,
) -> list[RowExtraction]:
    """Deterministic computation of (effect, SE) per row from confirmed
    whisker-cap handle positions. Native-scale output (log for log plots,
    linear for linear plots).

    Raises ConfidenceLevelInvalidError, HandlesCrossedError, plus any image
    decoding errors from _decode_and_validate_image.
    """
    if not (0.0 < conf_level < 1.0):
        raise ConfidenceLevelInvalidError(
            f"conf_level must be in (0, 1), got {conf_level}"
        )
    # Validates image even though math only needs pixel coords — symmetry
    # with propose_whisker_caps, plus early rejection of bad bundles.
    _decode_and_validate_image(image_bytes)

    m, b = _calibration_params(calibration)
    z = stats.norm.ppf((1.0 + conf_level) / 2.0)

    cal_p_lo = min(calibration.ref_pixel_1, calibration.ref_pixel_2)
    cal_p_hi = max(calibration.ref_pixel_1, calibration.ref_pixel_2)

    results: list[RowExtraction] = []
    for row in rows:
        if row.lower_handle_x >= row.upper_handle_x:
            raise HandlesCrossedError(
                f"lower_handle_x ({row.lower_handle_x}) must be strictly "
                f"less than upper_handle_x ({row.upper_handle_x})"
            )
        value_lo = m * row.lower_handle_x + b
        value_hi = m * row.upper_handle_x + b
        effect = (value_lo + value_hi) / 2.0
        se = (value_hi - value_lo) / (2.0 * z)
        outside = (
            row.lower_handle_x < cal_p_lo or row.lower_handle_x > cal_p_hi
            or row.upper_handle_x < cal_p_lo or row.upper_handle_x > cal_p_hi
        )
        audit = {
            "lower_x": int(row.lower_handle_x),
            "upper_x": int(row.upper_handle_x),
            "click_y": int(row.click_y),
            "pixel_delta": int(row.upper_handle_x - row.lower_handle_x),
            "z_value": float(z),
            "assumed_symmetric_ci": True,
            "handle_outside_calibration_span": bool(outside),
        }
        results.append(RowExtraction(
            effect=float(effect),
            se=float(abs(se)),
            conf_level=float(conf_level),
            scale=calibration.scale,
            audit=audit,
        ))
    return results


def build_figure_bundle(
    image_bytes: bytes,
    calibration: Calibration,
    rows: list[RowClick],
    conf_level: float = 0.95,
    engine_version: str = "0.1.1",
) -> FigureExtractionBundle:
    """Convenience: compute results + package into a TruthCert-ready bundle.

    The caller is responsible for feeding the bundle through
    truthcert.sign_bundle (after asdict-serialisation) if signing is
    desired.
    """
    results = extract_se_from_figure(image_bytes, calibration, rows, conf_level)
    return FigureExtractionBundle(
        image_sha256=hashlib.sha256(image_bytes).hexdigest(),
        calibration=calibration,
        rows=list(rows),
        conf_level=conf_level,
        results=results,
        engine_version=engine_version,
        timestamp_iso=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


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
