# Impossible Pooling v0.2.0 — Phase 0 Design

**Date:** 2026-04-23
**Scope:** Phase 0 of the 5-phase promotion of pilot winners (extreme_het, disconnected_nma) into the shipped `impossible-ma` package.
**Status:** design approved chunk-by-chunk by user; ready for implementation plan.
**Precedent:** [Impossible Pooling Pilot design](2026-04-23-impossible-pooling-pilot-design.md) and [pilot plan](../plans/2026-04-23-impossible-pooling-pilot.md).

## Context

The 2026-04-23 pilot (shipped via PR #1, merged at `80ad842`) triaged four "impossible pooling" flavours in `experiments/` and produced promotion-readiness scores:

| Flavour | Score | Status |
|---|---|---|
| `extreme_het` | 5/5 | ✓ Promote (this phase) |
| `disconnected_nma` | 4/5 | ✓ Promote (this phase) |
| `cross_framing` | 3/5 | Remains piloted; not promoted |
| `era_collision` | 3/5 | Remains piloted; not promoted |

The user selected **Option C** (shared infra, both flavours, phased) for promotion. That decomposes into 5 phases:

| Phase | Deliverable |
|---|---|
| **0 (this)** | Extend v0.1.1 API + port pilot code → `src/impossible_ma/` |
| 1 | R parity (metafor/netmeta to 1e-4) for both new flavours |
| 2 | E156 micro-paper drafts × 2 (one per flavour) |
| 3 | Pyodide HTML app with flavour selector |
| 4 | v0.2.0 ship: tag, Pages, Crossref DOI at publication |

This spec is **Phase 0 only**. Later phases get their own specs.

## Non-goals

- No R parity (Phase 1)
- No hypothesis property tests (deferred beyond Phase 2)
- No Pyodide HTML app updates (Phase 3)
- No paper drafts (Phase 2)
- No TruthCert HMAC signing of the two new cases (deferred)
- No MetaAudit adapter hooks for the new cases (deferred)
- No GitHub Pages regeneration (Phase 4)
- No Crossref DOI (minted at paper publication)
- No v0.2.0 git tag, no GitHub Release (Phase 4 cut)
- No reworking of shipped v0.1.1 modules (`kone`, `missing_se`, `adversarial`) — they stay as-is

Phase 0 is purely the API-surface extension + test-migration substrate.

## API shape decision (locked)

**Unified.** Extend `PossibilityEnvelope.case` from the 3-case Literal to 5. Drop the pilot's `PilotEnvelope.flavour` field — it was only needed because the pilot's `case` was free-form; now `case` carries the discriminator typed.

```python
# v0.1.1
Case = Literal["k1", "missing_se", "adversarial"]

# v0.2.0
Case = Literal["k1", "missing_se", "adversarial", "extreme_het", "disconnected_nma"]
```

Rationale (from brainstorming): the pilot's `to_possibility_envelope()` marker method in `PilotEnvelope` already pointed at this promotion path. Alternative "sibling type" and "base class + subclasses" options were rejected for fragmenting downstream consumers and adding inheritance overhead without engineering payoff.

## File structure after Phase 0

Working branch: `v0.2-phase0-port`, branched from master `80ad842` in an isolated worktree at `.worktrees/v0.2-phase0-port/`.

**Modified:**
- `src/impossible_ma/envelope.py` — extend `Case` Literal to 5 elements; add symmetric `lower=-inf` validation rule
- `pyproject.toml` — version `0.1.1` → `0.2.0`

**New under `src/impossible_ma/`:**
- `_pool.py` — `fe_pool`, `reml_pool`, `dl_tau2` (ported verbatim from `experiments/_pool.py`; leading underscore marks it internal)
- `extreme_het.py` — `run(case) -> PossibilityEnvelope` (ported from pilot; behaviour unchanged except `PilotEnvelope` → `PossibilityEnvelope` and `flavour` field dropped)
- `disconnected_nma.py` — `run(case) -> PossibilityEnvelope` with the **M1 REML upgrade** for bubble pools

**New under `tests/`:**
- `tests/test_extreme_het.py` — 4 behaviour tests, inlined fixture dicts (v0.1.1 style)
- `tests/test_disconnected_nma.py` — 4 behaviour tests, inlined fixture dicts, updated `min_info` string expectations to `"bubble_pool=REML"`
- `tests/test_pool.py` — 3 sanity tests (FE identical, REML τ²=0 homogeneous, DL τ² positive heterogeneous)

**Modified under `tests/`:**
- `tests/test_envelope_contract.py` — extend the case-validation parametrize to include the two new cases; add one test for the `lower=-inf` symmetric validation rule

**Deleted in `experiments/`:**
- `experiments/extreme_het.py` + `experiments/tests/test_extreme_het.py`
- `experiments/disconnected_nma.py` + `experiments/tests/test_disconnected_nma.py`
- `experiments/fixtures/extreme_het.json` + `experiments/fixtures/disconnected_nma.json`

**Kept unchanged (frozen pilot artifacts):**
- `experiments/pilot_envelope.py` — still imported by cross_framing + era_collision
- `experiments/_pool.py` — still imported by cross_framing + era_collision; note: duplicate with `src/impossible_ma/_pool.py`, acceptable because experiments/ is a pilot sandbox that must not depend on shipped src/
- `experiments/cross_framing.py`, `experiments/era_collision.py`, their tests, their fixture JSONs

**Modified in `experiments/`:**
- `experiments/compare.py` — updated to run only the 2 remaining (cross_framing, era_collision) pilot flavours; orphan imports of the deleted modules removed
- `experiments/comparison.md` — regenerated by the updated compare.py to show only 2 rows (the historical 4-row comparison stays in git at commit `06b424c`)
- `experiments/README.md` — promotion-readiness table: extreme_het and disconnected_nma rows rewritten to `"✓ Promoted to v0.2.0 (see src/impossible_ma/{flavour}.py)"`; cross_framing and era_collision rows unchanged with their 3/5 scores

**Untouched (shipped v0.1.1):**
- `src/impossible_ma/kone.py`, `missing_se.py`, `adversarial.py`, `cli.py`, `metaaudit_adapter.py`, `metaaudit_classifier.py`, `truthcert.py`
- Existing tests in `tests/` for the 3 old cases, R parity, MetaAudit, TruthCert

## `PossibilityEnvelope` invariant additions

Two diffs to `src/impossible_ma/envelope.py::__post_init__`:

```python
# already present (v0.1.1)
if math.isinf(self.upper) and "unbounded" not in self.min_info:
    raise ValueError("upper=inf requires 'unbounded' in min_info")

# new (v0.2.0) — symmetric for lower bound
if math.isinf(self.lower) and "unbounded" not in self.min_info:
    raise ValueError("lower=-inf requires 'unbounded' in min_info")
```

**SemVer call:** MINOR bump (`0.1.1` → `0.2.0`), not MAJOR:
- Adding Literal cases is additive — any v0.1.1 user code pattern-matching `"k1"`/`"missing_se"`/`"adversarial"` still type-checks
- The `lower=-inf` check is additive-restrictive and technically breaking, but grep of v0.1.1 shows zero code paths construct `lower=-math.inf`; zero real users affected
- CHANGELOG entry: *"If you construct `PossibilityEnvelope` directly with `lower=-math.inf`, include `'unbounded'` in `min_info`."*

## `_pool.py` port

Copy `experiments/_pool.py` verbatim into `src/impossible_ma/_pool.py`. Zero math changes. Three functions:

| Function | Returns | Purpose |
|---|---|---|
| `fe_pool(effects, variances)` | `(mu, se)` | Inverse-variance fixed-effect pool |
| `reml_pool(effects, variances, tau2_max=10.0)` | `(mu, se, tau2)` | Random-effects REML via `scipy.optimize.minimize_scalar` on 1-D REML log-likelihood |
| `dl_tau2(effects, variances)` | `tau2` | DerSimonian-Laird τ² (diagnostic use only — `advanced-stats.md` permits this for diagnostics) |

## `extreme_het.py` port

Three surface-level diffs from pilot:

1. Import: `from impossible_ma.envelope import PossibilityEnvelope` (was pilot envelope)
2. Return annotation: `-> PossibilityEnvelope`
3. Constructor: drop `flavour="extreme_het"` kwarg; `case="extreme_het"` carries the discriminator

**Unchanged:** refusal rule (`I² ≥ 0.80 OR τ̂/|δ̂_FE| ≥ 2.0`), study-level fallback when refused, REML pool when not refused, `min_info` strings (`"refused: …"` / `"pooled: …"`), assumptions dict, error on `k<3`.

## `disconnected_nma.py` port — REML bubble-pool upgrade

Three surface diffs (same as extreme_het), PLUS one math change: `_pool_bubble` upgrades from FE to REML for k≥2, preserving the k=1 short-circuit.

```python
from impossible_ma._pool import reml_pool  # was: fe_pool

def _pool_bubble(bubble: dict[str, Any]) -> tuple[float, float]:
    """Return (d_hat, var) for one bubble.

    k=1: short-circuits to the single study's (effect, se**2).
    k>=2: REML random-effects pool. Note: k=2 produces unstable tau^2
    estimates (per advanced-stats.md); k>=3 per bubble is preferred.
    """
    studies = bubble.get("studies")
    if studies is None or len(studies) == 0:
        raise ValueError("bubble has no studies (k=0)")
    effects = np.array([s["effect"] for s in studies], dtype=float)
    ses = np.array([s["se"] for s in studies], dtype=float)
    variances = ses ** 2
    if len(studies) == 1:
        return float(effects[0]), float(variances[0])
    mu, se, _tau2 = reml_pool(effects, variances)
    return mu, se ** 2
```

`min_info` change: `"bubble_pool=FE"` → `"bubble_pool=REML"` (cosmetic but spec-faithful).

**Test impact from the REML upgrade:**

| Test | Bubble k | Effect | Pass? |
|---|---|---|---|
| `test_tight_matches_classical` | k=1 each | short-circuit fires, `point≈0.05` | ✓ (unchanged) |
| `test_normal_bounded` | k=2 each | REML runs; test only checks finite bounds | ✓ (unchanged) |
| `test_unbounded_flagged` | k=1 each | short-circuit fires; unbounded branch unchanged | ✓ (unchanged) |
| `test_empty_bubble_raises` | k=0 | raises before pool | ✓ (unchanged) |

Rejected alternatives (from brainstorming):
- **FE for k=2, REML for k≥3**: hedges on the "spec said REML" story by dropping back to FE for the k=2 edge case
- **REML + Paule-Mandel initialization for k=2 stability**: over-engineers for a scenario unlikely in real clinical data (a disconnected NMA with exactly 2 studies per bubble is rare)

## Tests

11 new tests + 2-3 modifications:

| File | Action | Tests |
|---|---|---|
| `tests/test_extreme_het.py` | NEW | 4: `test_normal_refuses_point`, `test_tight_pools_with_point`, `test_unbounded_refuses_and_flags`, `test_k_lt_3_raises` |
| `tests/test_disconnected_nma.py` | NEW | 4: `test_normal_bounded`, `test_tight_matches_classical`, `test_unbounded_flagged`, `test_empty_bubble_raises` |
| `tests/test_pool.py` | NEW | 3: `test_fe_pool_identical_studies_equals_mean`, `test_reml_tau2_zero_when_no_heterogeneity`, `test_dl_tau2_positive_under_heterogeneity` |
| `tests/test_envelope_contract.py` | EXTEND | +2 new-case entries to case parametrize; +1 test for `lower=-inf` symmetric validation |

Test fixtures are **inlined as Python dicts** in each test file, matching v0.1.1's style. The pilot's JSON fixture files do not migrate; test cases reference inline dicts for self-contained readability.

Target shipped suite after Phase 0: **~168 engine tests** (154 v0.1.1 + 11 new + 3 contract extensions), all green. Selenium UI tests (22 environmental errors on this machine unrelated to Phase 0) unchanged.

## Error handling

Every error path is a `ValueError` with a field-naming message. No silent fallbacks. Unbounded envelopes are valid results (inf + `"unbounded"` marker), not errors.

| Source | Condition | Behaviour |
|---|---|---|
| `PossibilityEnvelope.__post_init__` | case not in Literal | `ValueError` naming `case` |
| same | `lower > upper` | `ValueError` |
| same | `point` outside bounds | `ValueError` |
| same | empty `min_info` | `ValueError` |
| same | `upper=inf` without `"unbounded"` in `min_info` | `ValueError` |
| same | `lower=-inf` without `"unbounded"` in `min_info` | `ValueError` (NEW) |
| `extreme_het.run` | `k<3` | `ValueError` with `impossible_ma.kone` pointer |
| `disconnected_nma.run` | missing `bubble_1` / `bubble_2` | `ValueError` |
| `disconnected_nma._pool_bubble` | k=0 bubble | `ValueError` |

## "Done" definition

1. `src/impossible_ma/envelope.py` has 5-case Literal + `lower=-inf` validation rule
2. `src/impossible_ma/_pool.py` exists with `fe_pool`, `reml_pool`, `dl_tau2`
3. `src/impossible_ma/extreme_het.py` exposes `run(case: dict) -> PossibilityEnvelope`
4. `src/impossible_ma/disconnected_nma.py` exposes `run(case: dict) -> PossibilityEnvelope` with the REML bubble-pool upgrade (k=1 short-circuit preserved)
5. `tests/` has the 11 new tests + 3 contract updates; the shipped suite still passes (~168 engine tests green, Selenium UI environmental errors unchanged)
6. `experiments/` cleanup done per §File-structure policy (2 promoted pilots deleted, 2 remaining pilots frozen, README updated, compare regenerated to 2 rows)
7. `pyproject.toml` bumped to `0.2.0`
8. Branch `v0.2-phase0-port` merged to `master` via PR
9. No tag, no release, no Pages deploy, no Crossref DOI — all deferred to Phase 4

## Risks / watch-points

1. **REML convergence on k=2 bubbles.** `scipy.optimize.minimize_scalar` handles it but often returns τ²=0 (REML reduces to FE). Pilot test tolerances (`abs=0.05` on the classical-collapse test) absorb any drift. **Risk:** low.
2. **`lower=-inf` validation is technically breaking.** Grep of v0.1.1 shows zero code paths construct `lower=-math.inf`. **Mitigation:** CHANGELOG entry + docstring note. **Risk:** ~zero real users.
3. **Duplicate `_pool.py` across `src/` and `experiments/`.** Intentional (experiments/ is a sandbox that must not depend on shipped src/). **Mitigation:** docstring comment in `experiments/_pool.py` marking src/ as canonical.
4. **`min_info` string change `FE` → `REML`.** Cosmetic but observable in `comparison.md` and any downstream consumer that parses `min_info`. **Mitigation:** regenerate comparison.md after Phase 0.
5. **Orphan imports in `experiments/compare.py`.** After deleting the 2 promoted pilots from experiments/, `compare.py` must be updated to import only cross_framing and era_collision. If the update is missed, compare.py breaks. **Mitigation:** covered as an explicit task in the plan.

## Time estimate

~1 session (1-3 hours) of subagent-driven work. Estimated 8-10 TDD tasks.

## Implementation plan

Generated separately via the `superpowers:writing-plans` skill after user review of this spec.
