import json
import shutil
import subprocess
from pathlib import Path

import pytest

from impossible_ma.missing_se import p_to_se, ci_to_se

RSCRIPT = shutil.which("Rscript") or r"C:\Program Files\R\R-4.5.2\bin\Rscript.exe"
SCRIPT = (
    Path(__file__).resolve().parents[1] / "r_scripts" / "missing_se_parity.R"
)


@pytest.mark.skipif(not Path(RSCRIPT).exists(), reason="Rscript not available")
def test_missing_se_parity(tmp_path):
    inp = {"effect": 0.5, "p_value": 0.04, "ci_lower": 0.1, "ci_upper": 0.9}
    in_json = tmp_path / "in.json"
    in_json.write_text(json.dumps(inp))
    out_json = tmp_path / "out.json"
    r = subprocess.run(
        [RSCRIPT, str(SCRIPT), str(in_json), str(out_json)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert r.returncode == 0, r.stderr
    r_out = json.loads(out_json.read_text())
    py_A = p_to_se(inp["effect"], inp["p_value"])
    py_B = ci_to_se(inp["ci_lower"], inp["ci_upper"])
    assert abs(py_A - r_out["A"]) < 1e-4
    assert abs(py_B - r_out["B"]) < 1e-4
