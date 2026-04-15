# Plan 1 Review — ImpossibleMA v1 Engine

## Summary
Plan 1 ships: Python engine for three ImpossibleMA cases (k=1, missing_se, adversarial) plus MetaAudit severity-signal validation pipeline.

## Scope
- **In scope (shipped):** PossibilityEnvelope dataclass, kone.py, missing_se.py, adversarial.py, metaaudit_adapter.py, metaaudit_classifier.py, truthcert.py, cli.py, headline_run.py.
- **Out of scope (Plan 2):** HTML app, Selenium, BMJ/F1000 manuscripts, GitHub repo + Pages.
- **Deferred (v1.1):** figure extraction (missing_se Route D — stubbed), auto-MeSH adjacent-trial lookup (kone).

## Test results
- **Total tests: 66, all passing** (~37s wall-clock)
- Breakdown:
  - envelope contract: 5
  - MetaAudit adapter: 5 (incl. real 68,519-row corpus read)
  - severity classifier: 11
  - kone: 7 + 1 R parity (metafor REML, 1e-4)
  - missing_se: 16 + 1 R parity (qnorm, 1e-4)
  - adversarial: 13 + 2 hypothesis property tests (23 random examples)
  - truthcert: 5
- Regression baselines pinned for kone, missing_se, adversarial at 1e-6 tolerance.

## Headline (pre-executed, Task 24)
- Corpus: `C:\MetaAudit\results\audit_results.csv` (68,519 rows, 6,229 unique MAs)
- **Denominator (MAs with ≥1 CRITICAL flag): 444**
- **Numerator (classified): 444 adversarial, 0 unclassified**
- Only CRITICAL-firing module in this corpus version: `prediction_gap`

## Plan deviations (all documented in commit messages)
1. **MetaAudit pivot (2026-04-15):** Plan assumed `reviews.csv` with author prose. Actual corpus is `audit_results.csv` with formal severity signals. Spec §5 and plan Tasks 3/4/24 rewritten. Commit `5b02aab9` on the user repo.
2. **RBesT dropped from R parity:** Not installed in target environment; `metafor::rma` gives the strict 1e-4 parity anyway. Task 7 revised.
3. **`prediction_gap` added to classifier priority:** Pivot-early-run exposed that `prediction_gap` is the only module escalating to CRITICAL; without it, numerator was 0. Added between `underpowered(k≤2)` and `fragility`. Commit `af3ca04`.
4. **missing_se envelope ordering:** Plan had `lower=widest SE, upper=narrowest SE` which violates PossibilityEnvelope's `lower ≤ upper` contract. Swapped to numeric ordering; conservative/liberal semantics moved to `assumptions` dict. Commit `1f55f30`.
5. **adversarial envelope widening:** Plan's significance-aware extremes didn't always contain `full_data_reml`. Added a `min(lower, full); max(upper, full)` step to satisfy the spec's property invariant. Commit `e5d1980`. Semantically sound: the unrestricted REML is itself a defensible pool member.

## File sizes (no refactor flagged)
- Largest module: `adversarial.py` at 199 lines (well under the 400-line threshold).
- Total: 1,436 lines of code + tests.

## Security
- TruthCert HMAC key from `TRUTHCERT_HMAC_KEY` env var or `~/.truthcert_key` file (≥32 bytes). Fails closed if neither present.
- Key is **never** derived from bundle contents.
- Signature comparison uses `hmac.compare_digest` (constant-time).

## Commits (20 total)
From oldest to newest:
1. `278b5dc` chore: add fail-closed preflight
2. `38e1f93` fix: align preflight with actual MetaAudit schema
3. `a135e22` feat: scaffold package
4. `9a2882b` feat: PossibilityEnvelope dataclass
5. `1e0ff35` feat: MetaAudit adapter
6. `612b591` feat: severity classifier
7. `b5e8bf8` feat: headline script (pre-executed)
8. `af3ca04` fix: prediction_gap priority (444/444)
9. `f3b58e5` feat: kone MAP via REML
10. `f94c5f8` feat: kone envelope
11. `f2ddc72` test: kone metafor parity
12. `a89f44a` test: kone regression baseline
13. `1f55f30` feat: missing_se 4 routes + envelope
14. `b51c597` test: missing_se R parity
15. `3fcf507` test: missing_se regression baseline
16. `e5d1980` feat: adversarial core
17. `a8c67fc` test: adversarial properties
18. `67c11f2` test: adversarial regression baseline
19. `ef81b53` feat: TruthCert HMAC bundle
20. `f0a9ce9` feat: CLI entry point

## Next: Plan 2
- Single-file HTML app (`impossible-ma.html`) with 3 tabs
- Selenium tests (~25)
- BMJ Methods manuscript anchored on 444/6,229
- F1000 software paper
- E156 micro-paper
- GitHub repo + Pages
- Zenodo DOI
