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
