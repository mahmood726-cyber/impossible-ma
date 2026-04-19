# v0.1.1 Review — Route D (figure extraction)

## Summary

v0.1.1 ships Route D of `missing_se`: semi-automatic (effect, SE) extraction from horizontal forest plot PNG/JPG. User calibrates the x-axis with two typed tick values; per-row workflow is one click → edge-detected whisker-cap handles → confirm. Python engine authoritative; browser owns the UX; CLI replays via `{"route":"D"}` JSON spec.

## Acceptance

- [x] `extract_se_from_figure` implemented; `figure_to_se` stub removed (commit `3373fab`)
- [x] 20-fixture matplotlib test corpus committed (524 KB)
- [x] Pytest: 154 tests pass (engine, `tests/ --ignore=tests/test_ui.py`)
- [x] Hypothesis property tests pass (50 examples each for log + linear)
- [x] Selenium UI tests: 3 new Route D flows pass (`test_route_d_calibration_flow`, `test_route_d_one_row_flow`, `test_route_d_multi_row_send_to_b`)
- [x] TruthCert round-trip verified
- [x] CLI `"route":"D"` replay path works
- [x] Manuscripts updated (e156 S7, f1000 x2, bmj_methods §5.2)
- [x] Version bumped (pyproject.toml + CITATION.cff)
- [x] Pages rebuild will pick up the new HTML on next push

## Commits

Phase 1 (engine, 11 commits): `0ad3bfd..3373fab`
Phase 2 (HTML + Selenium, 4 commits): `3373fab..ce0dfaf`
Phase 3 (release): current phase, 3 commits expected

## Public URLs (post-release)

- Repo: https://github.com/mahmood726-cyber/impossible-ma
- Pages: https://mahmood726-cyber.github.io/impossible-ma/ (redirect → impossible-ma.html)
- Release: https://github.com/mahmood726-cyber/impossible-ma/releases/tag/v0.1.1 (pending tag push)

## Scope note — known limitations shipped with the release

- `propose_whisker_caps` uses leftmost/rightmost policy + background-band subtraction; works well on clean horizontal forest plots. Plots with null-effect axvlines, axis gridlines, or annotation arrows may produce noisy proposals — the user-in-the-loop drag-correct flow handles these.
- Calibration bbox (plot-area x-range) derived from calibration clicks; works when calibration is at plot-area edges. The fixture corpus was regenerated with this convention; production plots may require wider bbox via UI.
- Route D supports ONE figure at a time; multi-figure extraction is a v0.1.2+ scope item.

## Deferred to v0.1.2+

- Asymmetric-CI mode (effect as separate third draggable handle)
- Batch / auto-detect rows from a figure (no per-row clicks required)
- Vertical error bars (Route E or Route D option)
- auto-MeSH for kone (its own brainstorm / plan pending)
- Dashed-line residue suppression in `propose_whisker_caps` (for plots with null-effect axvlines)

## Acknowledged drifts from the plan (from code-review iterations)

- `_PEAK_MIN_SEPARATION = 3` separate from `_MIN_CAP_SEPARATION = 10` (plan had them conflated; code-review split them — Task 4 commit)
- NaN/inf guard added to `Calibration.__post_init__` (Task 2 code review → Task 7 commit)
- `search_x_range` optional parameter on `propose_whisker_caps` + background-band subtraction (Task 6 required these to survive matplotlib-rendered fixtures — Task 6 commit)
- Fixtures regenerated without `ax.axvline` + calibration at plot-area edges (Task 5/6 fix)
- Pillow added to Pyodide bootstrap (fixed a pre-existing silent bug surfaced by the Selenium tests — Task 17-19 commit)
- CLI Route D route-dispatch inside `_run_missing_se` (plan suggested CLI flags, used payload-key-based dispatch to fit existing runner contract)
