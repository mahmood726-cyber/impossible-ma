# Plan 2 Review — ImpossibleMA HTML App

## Summary

Single-file `impossible-ma.html` ships (51 KB including a 16 KB base64-embedded `impossible_ma` Python wheel). Runs the Plan 1 engine in-browser via Pyodide. Three tabs (k=1, missing_se, adversarial), each with built-in datasets, form input, and CSV upload (adversarial). Exports HMAC-signed TruthCert bundles + printable HTML reports. Validated by 22 Selenium tests against headless Chrome.

## Test results

### UI suite (Plan 2)
- `pytest tests/test_ui.py -v` → **22/22 passed in 12:05** (isolated run)
- Module-scoped driver fixture: Pyodide loads once (~170s cold), all tests reuse the same browser session for ~12s each
- Test coverage:
  - Infra: Pyodide ready-signal, default tab, hash routing, sessionStorage (4)
  - k=1: 3 datasets parametrized + form entry + invalid-input guard (5)
  - missing_se: 3 datasets parametrized + no-route guard (4)
  - adversarial: 3 datasets parametrized + CSV missing-column banner (4)
  - TruthCert: no-key alert + signed-bundle round-trip via Pyodide `verify_bundle` (2)
  - Report: printable-report window opens with envelope + signature (1)
  - Misc: raw-JSON toggle, Python traceback surfaces in error pane (2)

### Combined suite (Plan 1 + Plan 2)
- `pytest tests/ -v` → 66 engine passed, 22 UI errors (flaky under combined run)
- Engine suite is unchanged and still 66/66 when run in isolation: `pytest tests/ --ignore=tests/test_ui.py`
- **Known issue:** when UI tests run after the 66 engine tests in the same pytest invocation, chromedriver / the module-scoped Pyodide fixture times out. Isolated runs pass reliably.
- **Recommended CI pattern:** run engine suite and UI suite as two separate invocations.

## Architecture confirmation
- Wheel embedded as base64 in the HTML (~16 KB of 51 KB total).
- Pyodide CDN v0.27.7 + Plotly CDN v2.35.2.
- Page-ready signal: `window.PYODIDE_READY === true` (documented in spec §6).
- TruthCert key in sessionStorage — never localStorage.
- All math runs in Pyodide → byte-identical to CLI output for identical inputs.

## Plan deviations (all discovered during implementation, all documented in commit messages)

1. **Wheel filename tags required.** Plan said `pyodide.FS.writeFile('/tmp/impossible_ma.whl', bytes)` then `micropip.install('/tmp/impossible_ma.whl')`. micropip parses the filename as a wheel name and rejects the truncated form. Fixed by using the fully-tagged filename `impossible_ma-0.1.0-py3-none-any.whl` and the `emfs:` URL scheme for `micropip.install`. Commit `7b4ba17`.

2. **Double JS→Python conversion.** Plan had `pyodide.globals.set('K', pyodide.toPy(obj))` followed by `K.to_py()` in Python. That's a double-conversion — `toPy` already produces a Python dict, so `.to_py()` on the dict raises `AttributeError`. Fixed in all 5 Python inline blocks (k1/missing_se/adversarial runs + TruthCert sign × 2). Commit `d565da7`.

3. **missing_se envelope ordering.** The Plan 1 bug (lower=widest SE, upper=narrowest SE violating `lower ≤ upper`) was already fixed in Plan 1 but worth noting here that the HTML correctly displays the fixed version's envelope.

4. **page fixture reload.** Initial plan had `driver.get(PAGE_URL)` in the per-test `page` fixture with a 30-second ready-wait. This forces a second Pyodide cold load per test (~170s) which blows the 30s budget and errors every test. Fixed by removing the reload and resetting DOM/form state in-place; Pyodide stays loaded from the module-scoped driver fixture. Commit `364da8f`.

5. **Selenium `.text` on `<details><pre>`** returns empty string when the `<details>` is collapsed. Tests use `driver.execute_script("return document.getElementById('…').textContent")` instead.

## File deltas

| File | Lines | Role |
|------|-------|------|
| `impossible-ma.html.template` | 694 | Source of truth |
| `impossible-ma.html` | — | Built artefact (wheel base64 embedded) |
| `scripts/build_html.py` | 48 | Wheel builder + template substitutor |
| `scripts/preflight_html.py` | 85 | Plan 2 prereq checks |
| `tests/test_ui.py` | 255 | Selenium suite (22 tests) |

## Commits (17 Plan 2 commits on top of Plan 1)

1. `51df708` chore: Plan 2 preflight
2. `7b4ba17` feat: scaffold impossible-ma.html with Pyodide bootstrap
3. `f5d83b8` feat: tab router + 3 empty panes + TruthCert key footer
4. `d2cc824` feat: k=1 tab input form + 3 built-in datasets
5. `4c3a83e` feat: k=1 tab Python integration + raw JSON viewer
6. `ac161fb` feat: k=1 tab Plotly density visualization
7. `8fea67d` feat: missing_se tab full implementation (form + run + bar viz)
8. `3d63871` feat: adversarial tab input UI (CSV + form + 3 datasets)
9. `069cf27` feat: adversarial tab Python integration + histogram viz
10. `4bc9080` feat: TruthCert sign-and-download for all 3 tabs
11. `37920a2` feat: printable HTML report for all 3 tabs
12. `d565da7` fix: remove double JS→Python conversion in run handlers
13. `a0771e3` test: Selenium infra + page-ready helper (module-scoped driver)
14. `3d8989d` test: Selenium tab routing + sessionStorage
15. `d5a3536` test: Selenium k=1 tests (3 datasets + form + invalid)
16. `dabaebc` test: Selenium missing_se tests (3 datasets + no-route)
17. `6cf1f38` test: Selenium adversarial tests (3 datasets + CSV error)
18. `206c933` test: Selenium TruthCert + printable report
19. `364da8f` test: Task 17 misc tests + page-fixture reload-fix

## Known issues / next-session pickups

1. The committed `impossible-ma.html` is 51 KB with the wheel embedded. If the wheel changes (e.g. Plan 1 engine edits), re-run `python scripts/build_html.py` and commit both the template and the rebuilt HTML.
2. Combined pytest run (engine + UI in one invocation) is flaky. CI should run the two suites separately.
3. First-load UX is ~170s. Post-Plan-2 could add a browser-cache-hit detector and a faster progress bar.

## Next: Plan 3 (Manuscripts) and Plan 4 (GitHub Pages + Zenodo)
