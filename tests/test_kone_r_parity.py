import json
import shutil
import subprocess
from pathlib import Path

import pandas as pd
import pytest

from impossible_ma.kone import fit_map_prior

RSCRIPT = shutil.which("Rscript") or r"C:\Program Files\R\R-4.5.2\bin\Rscript.exe"
METAFOR_SCRIPT = (
    Path(__file__).resolve().parents[1] / "r_scripts" / "kone_parity_metafor.R"
)
FIXTURES = Path(__file__).parent / "fixtures"


@pytest.mark.skipif(not Path(RSCRIPT).exists(), reason="Rscript not available")
def test_kone_reml_parity_with_metafor(tmp_path):
    df = pd.read_csv(FIXTURES / "adjacent_trials.csv")
    adjacent = list(zip(df["estimate"], df["se"]))
    in_json = tmp_path / "in.json"
    in_json.write_text(json.dumps({
        "estimate": df["estimate"].tolist(),
        "se": df["se"].tolist(),
    }))
    out_json = tmp_path / "out.json"
    r = subprocess.run(
        [RSCRIPT, str(METAFOR_SCRIPT), str(in_json), str(out_json)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert r.returncode == 0, r.stderr
    r_out = json.loads(out_json.read_text())
    py_fit = fit_map_prior(adjacent)
    assert abs(py_fit["mu"] - r_out["mu"]) < 1e-4, (
        f"mu mismatch: py={py_fit['mu']} r={r_out['mu']}"
    )
    assert abs(py_fit["mu_se"] - r_out["mu_se"]) < 1e-4
    assert abs(py_fit["tau"] - r_out["tau"]) < 1e-3
