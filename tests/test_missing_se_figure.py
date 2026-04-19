"""Pytest suite for Route D (figure extraction) of missing_se."""
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
