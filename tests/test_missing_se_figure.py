"""Pytest suite for Route D (figure extraction) of missing_se."""
import json
import pytest

from impossible_ma.missing_se import (
    FigureExtractionError,
    UnsupportedFigureFormatError,
    ImageTooSmallError,
    ImageTooLargeError,
    CalibrationError,
    ClickYOutOfBoundsError,
    NoWhiskerCapsDetectedError,
    WhiskerCapsTooCloseError,
    HandlesCrossedError,
    ConfidenceLevelInvalidError,
)


@pytest.mark.parametrize(
    "exc",
    [
        UnsupportedFigureFormatError,
        ImageTooSmallError,
        ImageTooLargeError,
        CalibrationError,
        ClickYOutOfBoundsError,
        NoWhiskerCapsDetectedError,
        WhiskerCapsTooCloseError,
        HandlesCrossedError,
        ConfidenceLevelInvalidError,
    ],
)
def test_exception_subclasses_base(exc):
    assert issubclass(exc, FigureExtractionError)
    # Exception must carry a message
    instance = exc("test message")
    assert "test message" in str(instance)


from impossible_ma.missing_se import (
    Calibration, RowClick, RowExtraction, FigureExtractionBundle,
)


class TestCalibration:
    def test_valid_log(self):
        c = Calibration(scale="log", ref_pixel_1=100, ref_value_1=0.5,
                        ref_pixel_2=300, ref_value_2=2.0)
        assert c.scale == "log"

    def test_valid_linear(self):
        c = Calibration(scale="linear", ref_pixel_1=50, ref_value_1=-1.0,
                        ref_pixel_2=450, ref_value_2=1.0)
        assert c.scale == "linear"

    def test_coincident_pixels_rejected(self):
        with pytest.raises(CalibrationError, match="distinct pixel"):
            Calibration(scale="log", ref_pixel_1=100, ref_value_1=0.5,
                        ref_pixel_2=100, ref_value_2=2.0)

    def test_equal_values_rejected(self):
        with pytest.raises(CalibrationError, match="distinct value"):
            Calibration(scale="log", ref_pixel_1=100, ref_value_1=1.0,
                        ref_pixel_2=300, ref_value_2=1.0)

    def test_log_requires_positive(self):
        with pytest.raises(CalibrationError, match="positive"):
            Calibration(scale="log", ref_pixel_1=100, ref_value_1=-0.5,
                        ref_pixel_2=300, ref_value_2=2.0)
        with pytest.raises(CalibrationError, match="positive"):
            Calibration(scale="log", ref_pixel_1=100, ref_value_1=0.5,
                        ref_pixel_2=300, ref_value_2=0.0)

    def test_invalid_scale_rejected(self):
        with pytest.raises(CalibrationError, match="scale"):
            Calibration(scale="polar", ref_pixel_1=100, ref_value_1=0.5,  # type: ignore
                        ref_pixel_2=300, ref_value_2=2.0)


class TestRowClick:
    def test_valid(self):
        r = RowClick(click_y=150, lower_handle_x=120, upper_handle_x=280)
        assert r.label is None

    def test_with_label(self):
        r = RowClick(click_y=150, lower_handle_x=120, upper_handle_x=280,
                     label="Study A")
        assert r.label == "Study A"


def test_row_extraction_shape():
    rx = RowExtraction(effect=-0.1, se=0.08, conf_level=0.95, scale="log",
                       audit={"lower_x": 120, "upper_x": 280})
    assert rx.effect == -0.1
    assert rx.scale == "log"


def test_bundle_shape():
    c = Calibration(scale="log", ref_pixel_1=100, ref_value_1=0.5,
                    ref_pixel_2=300, ref_value_2=2.0)
    r = RowClick(click_y=150, lower_handle_x=120, upper_handle_x=280)
    rx = RowExtraction(effect=-0.1, se=0.08, conf_level=0.95, scale="log",
                       audit={})
    b = FigureExtractionBundle(
        image_sha256="a" * 64,
        calibration=c,
        rows=[r],
        conf_level=0.95,
        results=[rx],
        engine_version="0.1.1",
        timestamp_iso="2026-04-18T12:00:00Z",
    )
    assert b.image_sha256 == "a" * 64


def test_base_inherits_value_error():
    """Lock the load-bearing ValueError root — callers with
    `except ValueError:` handlers must continue to work as Route D
    starts raising these in Tasks 3/4/7."""
    assert issubclass(FigureExtractionError, ValueError)


import io
from PIL import Image
import numpy as np

from impossible_ma.missing_se import _decode_and_validate_image


def _png_bytes(width: int, height: int, fill: int = 255) -> bytes:
    """Build a solid-colour grayscale PNG for testing."""
    buf = io.BytesIO()
    Image.new("L", (width, height), fill).save(buf, format="PNG")
    return buf.getvalue()


def _jpg_bytes(width: int, height: int, quality: int = 95) -> bytes:
    buf = io.BytesIO()
    Image.new("L", (width, height), 255).save(buf, format="JPEG", quality=quality)
    return buf.getvalue()


class TestDecode:
    def test_png_ok(self):
        arr = _decode_and_validate_image(_png_bytes(400, 300))
        assert arr.shape == (300, 400)
        assert arr.dtype == np.uint8

    def test_jpg_ok(self):
        arr = _decode_and_validate_image(_jpg_bytes(400, 300))
        assert arr.shape == (300, 400)

    def test_tiff_rejected(self):
        buf = io.BytesIO()
        Image.new("L", (400, 300), 255).save(buf, format="TIFF")
        with pytest.raises(UnsupportedFigureFormatError, match="PNG or JPG"):
            _decode_and_validate_image(buf.getvalue())

    def test_corrupted_bytes_rejected(self):
        with pytest.raises(UnsupportedFigureFormatError):
            _decode_and_validate_image(b"not an image")

    def test_too_small_rejected(self):
        with pytest.raises(ImageTooSmallError, match="too small"):
            _decode_and_validate_image(_png_bytes(50, 300))
        with pytest.raises(ImageTooSmallError):
            _decode_and_validate_image(_png_bytes(400, 50))

    def test_too_large_rejected(self):
        # Size gate fires before any Pillow decoding. Using raw bytes makes the
        # test deterministic regardless of PNG compression behaviour — the whole
        # point of the size-first ordering is that we don't spend memory
        # decoding oversized payloads, so this also validates the ordering.
        with pytest.raises(ImageTooLargeError, match="10 MB"):
            _decode_and_validate_image(b"\x00" * 10_000_001)

    def test_decompression_bomb_rejected(self):
        """A small PNG declaring very large dimensions should map to
        ImageTooLargeError (not leak as PIL.Image.DecompressionBombError).
        15000×15000 solid-L PNG is ~250 KB encoded but 225 MP decoded,
        well past Pillow's default 89 MP bomb threshold."""
        buf = io.BytesIO()
        Image.new("L", (15000, 15000), 255).save(buf, format="PNG")
        with pytest.raises(ImageTooLargeError):
            _decode_and_validate_image(buf.getvalue())

    def test_truncated_image_rejected(self):
        """A truncated PNG passes Image.open() (lazy) but fails on convert().
        Must be translated to UnsupportedFigureFormatError."""
        full = _png_bytes(400, 300)
        # Take enough bytes to keep the PNG header valid (Image.open succeeds)
        # but not enough for the IDAT chunk to decode (convert("L") fails).
        truncated = full[: len(full) // 2]
        with pytest.raises(UnsupportedFigureFormatError, match="truncated|decode"):
            _decode_and_validate_image(truncated)


from impossible_ma.missing_se import propose_whisker_caps


def _synthetic_whisker_image(
    width: int, height: int, row_y: int,
    lower_x: int, upper_x: int,
    marker_x: int | None = None,
) -> bytes:
    """Create a test image with two short vertical whisker caps and an
    optional midpoint marker. Returns PNG bytes.
    """
    arr = np.full((height, width), 255, dtype=np.uint8)  # white background
    # horizontal bar between whiskers (dark, thin)
    arr[row_y, lower_x:upper_x + 1] = 0
    # whisker caps: short vertical lines, ±3 px from row_y
    arr[row_y - 3:row_y + 4, lower_x] = 0
    arr[row_y - 3:row_y + 4, upper_x] = 0
    # optional marker (small filled square)
    if marker_x is not None:
        arr[row_y - 2:row_y + 3, marker_x - 2:marker_x + 3] = 0
    buf = io.BytesIO()
    # Pillow auto-detects L mode from 2-D uint8; avoids mode= deprecation.
    Image.fromarray(arr).save(buf, format="PNG")
    return buf.getvalue()


class TestProposeWhiskerCaps:
    def test_detects_both_caps(self):
        img = _synthetic_whisker_image(400, 200, row_y=100,
                                       lower_x=120, upper_x=280,
                                       marker_x=200)
        lo, hi = propose_whisker_caps(img, click_y=100)
        assert abs(lo - 120) <= 1
        assert abs(hi - 280) <= 1

    def test_click_y_out_of_bounds_raises(self):
        img = _synthetic_whisker_image(400, 200, row_y=100,
                                       lower_x=120, upper_x=280)
        with pytest.raises(ClickYOutOfBoundsError):
            propose_whisker_caps(img, click_y=-5)
        with pytest.raises(ClickYOutOfBoundsError):
            propose_whisker_caps(img, click_y=250)

    def test_no_whiskers_raises(self):
        # solid white image: no edges at all
        buf = io.BytesIO()
        Image.new("L", (400, 200), 255).save(buf, format="PNG")
        with pytest.raises(NoWhiskerCapsDetectedError):
            propose_whisker_caps(buf.getvalue(), click_y=100)

    def test_too_close_raises(self):
        img = _synthetic_whisker_image(400, 200, row_y=100,
                                       lower_x=198, upper_x=202)
        with pytest.raises(WhiskerCapsTooCloseError):
            propose_whisker_caps(img, click_y=100)

    def test_off_row_still_finds_if_in_band(self):
        img = _synthetic_whisker_image(400, 200, row_y=100,
                                       lower_x=120, upper_x=280)
        # click_y 102 is within band_height=7 (centred on 100 → 97–103)
        lo, hi = propose_whisker_caps(img, click_y=102)
        assert abs(lo - 120) <= 1
        assert abs(hi - 280) <= 1

    def test_band_height_zero_raises(self):
        img = _synthetic_whisker_image(400, 200, row_y=100,
                                       lower_x=120, upper_x=280)
        with pytest.raises(ValueError, match="band_height"):
            propose_whisker_caps(img, click_y=100, band_height=0)
        with pytest.raises(ValueError, match="band_height"):
            propose_whisker_caps(img, click_y=100, band_height=-1)

    def test_sparse_noise_does_not_register_as_cap(self):
        """Tiny-magnitude gradient features (grey 254 vs white 255) must not
        register as caps once the MAD-floor is in place."""
        arr = np.full((200, 400), 255, dtype=np.uint8)
        arr[100, 50] = 254   # single-pixel noise, magnitude 1 after gradient
        arr[100, 200] = 254  # second single-pixel noise
        buf = io.BytesIO()
        Image.fromarray(arr).save(buf, format="PNG")
        with pytest.raises(NoWhiskerCapsDetectedError):
            propose_whisker_caps(buf.getvalue(), click_y=100)

    def test_search_x_range_excludes_gutter_features(self):
        """A single-pixel noise in the gutter (x=10) must not win as the
        leftmost cap when search_x_range excludes the gutter."""
        arr = np.full((200, 400), 255, dtype=np.uint8)
        arr[100, 10] = 0
        arr[97:104, 120] = 0
        arr[97:104, 280] = 0
        arr[100, 120:281] = 0
        buf = io.BytesIO()
        Image.fromarray(arr).save(buf, format="PNG")
        img = buf.getvalue()
        lo, hi = propose_whisker_caps(img, click_y=100, search_x_range=(100, 300))
        assert abs(lo - 120) <= 1
        assert abs(hi - 280) <= 1

    def test_search_x_range_invalid_raises(self):
        img = _synthetic_whisker_image(400, 200, row_y=100,
                                       lower_x=120, upper_x=280)
        with pytest.raises(ValueError, match="search_x_range"):
            propose_whisker_caps(img, click_y=100, search_x_range=(-1, 100))
        with pytest.raises(ValueError, match="search_x_range"):
            propose_whisker_caps(img, click_y=100, search_x_range=(100, 100))
        with pytest.raises(ValueError, match="search_x_range"):
            propose_whisker_caps(img, click_y=100, search_x_range=(100, 500))


from pathlib import Path

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "figure_corpus"


def _fixture_ids():
    return sorted(
        p.name.replace(".truth.json", "")
        for p in FIXTURE_DIR.glob("*.truth.json")
    )


@pytest.fixture(params=_fixture_ids())
def fixture_data(request):
    stem = request.param
    truth_path = FIXTURE_DIR / f"{stem}.truth.json"
    truth = json.loads(truth_path.read_text(encoding="utf-8"))
    ext = "png" if truth["format"] == "png" else "jpg"
    img_bytes = (FIXTURE_DIR / f"{stem}.{ext}").read_bytes()
    return truth, img_bytes


def _calibration_bbox(truth: dict) -> tuple[int, int]:
    """Derive the search x-range from calibration clicks: the calibration
    points sit at the plot-area edges, so shrink INWARD by 2 px to exclude
    the axis spine pixels themselves (spine edges produce saturated
    gradient peaks that bg-subtraction only partially suppresses when the
    search range includes the exact spine column)."""
    p1 = truth["calibration_clicks"][0]["pixel_x"]
    p2 = truth["calibration_clicks"][1]["pixel_x"]
    lo, hi = min(p1, p2), max(p1, p2)
    pad = 2
    x_lo = min(lo + pad, hi - 1)
    x_hi = max(hi - pad, lo + 1)
    if x_lo >= x_hi:
        x_lo, x_hi = lo, hi
    return x_lo, x_hi


# Per-fixture tolerance overrides. Default is ±3 px; JPG Q70 fixtures
# are allowed ±4 px because JPEG mosquito-noise ringing near high-contrast
# edges creates above-floor gradient residue 3-4 px away from the true
# cap column, which the leftmost/rightmost peak picker can snap to.
_ROUND_TRIP_TOLERANCE = {
    "lin_narrow_sq_800_jpg70": 4,  # JPEG Q70 mosquito-noise ringing
}


def test_propose_whisker_caps_round_trip(fixture_data):
    truth, img = fixture_data
    bbox = _calibration_bbox(truth)
    tol = _ROUND_TRIP_TOLERANCE.get(truth["slug"], 3)
    for study in truth["studies"]:
        lo, hi = propose_whisker_caps(
            img, click_y=study["click_y"], search_x_range=bbox
        )
        assert abs(lo - study["lower_x_true"]) <= tol, (
            f"lower cap off by {lo - study['lower_x_true']} px "
            f"in {truth['slug']}:{study['label']} (tol={tol})"
        )
        assert abs(hi - study["upper_x_true"]) <= tol, (
            f"upper cap off by {hi - study['upper_x_true']} px "
            f"in {truth['slug']}:{study['label']} (tol={tol})"
        )
