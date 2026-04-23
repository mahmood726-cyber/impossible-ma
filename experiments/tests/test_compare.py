from pathlib import Path

import pytest

from experiments.compare import run_all


def test_run_all_produces_markdown_with_remaining_pilot_rows(tmp_path: Path):
    out = tmp_path / "comparison.md"
    run_all(output_path=out)
    content = out.read_text()
    # Only the 2 non-promoted pilots remain after Phase 0 (Option C):
    assert "cross_framing" in content
    assert "era_collision" in content
    # Promoted flavours are no longer in the pilot harness:
    assert "disconnected_nma" not in content
    assert "extreme_het" not in content


def test_run_all_includes_both_tables(tmp_path: Path):
    out = tmp_path / "comparison.md"
    run_all(output_path=out)
    content = out.read_text()
    assert "normal-case comparison" in content.lower()
    assert "degenerate" in content.lower()
