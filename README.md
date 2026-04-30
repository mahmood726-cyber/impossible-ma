# ImpossibleMA

Bounded synthesis for Cochrane meta-analyses declared unpoolable.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests: 88/88](https://img.shields.io/badge/Tests-88%2F88-brightgreen.svg)](#testing)

## What

Textbook meta-analysis declares three classes of evidence "unpoolable": a single pivotal trial (k=1), studies with missing standard errors, or questions where defensible inclusion rules produce conflicting pooled estimates. ImpossibleMA implements a unifying primitive — the **Possibility Envelope** `(lower, upper, point|None, min_info, assumptions)` — that converts each impossibility into a bounded range of defensible pooled effects, plus a single named datum that would collapse the envelope to a point.

Applied to the 6,229 Cochrane meta-analyses in the MetaAudit corpus, 444 (7.13%) carry at least one CRITICAL audit flag. ImpossibleMA converts all 444 into bounded envelopes via the adversarial module.

## Run in the browser

**https://mahmood726-cyber.github.io/impossible-ma/impossible-ma.html** — single-file HTML app, no install. Pyodide first-load ~3 minutes; subsequent loads cached.

## Run locally

Selenium UI tests are excluded from the default test run (3-minute Pyodide cold start). Run them on demand with `-m selenium`.

```bash
git clone https://github.com/mahmood726-cyber/impossible-ma.git
cd impossible-ma
pip install -e .
pytest tests/                              # engine: 66 tests (default; ~37s)
pytest -m selenium tests/                  # HTML/Selenium: 22 tests (~12 min cold)
```

CLI:
```bash
echo '{"target_estimate":-0.5,"target_se":0.25,"endpoint":"binary","adjacent":[[-0.3,0.15],[-0.25,0.12],[-0.4,0.18],[-0.2,0.2],[-0.35,0.1]]}' > k1.json
impossible-ma k1 k1.json --sign
```

## What's where

- `src/impossible_ma/` — Python engine (envelope dataclass, k=1, missing_se, adversarial, TruthCert, CLI)
- `impossible-ma.html` — single-file browser app (51 KB, Pyodide + Plotly)
- `tests/` — 66 engine + 22 Selenium
- `paper/` — E156, F1000, BMJ Methods drafts + shared refs.bib + 3 figures
- `scripts/` — preflight, build_html, headline_run, export_figures

## Headline

Of 6,229 Cochrane meta-analyses in MetaAudit, 444 (7.13%) carry at least one CRITICAL audit flag; ImpossibleMA converts all 444 into bounded Possibility Envelopes. See `scripts/headline_output.json`.

## Testing

88 automated tests gate every commit:
- R parity to 1e-4 against `metafor::rma(method="REML")` (kone) and qnorm-based reconstruction (missing_se)
- Property tests via `hypothesis` for envelope monotonicity and full-data-REML containment
- Regression baselines pinned at 1e-6
- Selenium suite runs the HTML app end-to-end in headless Chrome

## License

MIT. See `LICENSE`.

## Cite

See `CITATION.cff`. Formal citation via Synthesis journal when the software paper is published (DOI pending submission).
