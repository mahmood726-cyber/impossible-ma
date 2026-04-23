from pathlib import Path

import pytest

from experiments.compare import run_all


def test_run_all_produces_markdown_with_four_rows(tmp_path: Path):
    out = tmp_path / "comparison.md"
    run_all(output_path=out)
    content = out.read_text()
    assert "disconnected_nma" in content
    assert "extreme_het" in content
    assert "cross_framing" in content
    assert "era_collision" in content


def test_run_all_includes_both_tables(tmp_path: Path):
    out = tmp_path / "comparison.md"
    run_all(output_path=out)
    content = out.read_text()
    assert "normal-case comparison" in content.lower()
    assert "degenerate" in content.lower()
