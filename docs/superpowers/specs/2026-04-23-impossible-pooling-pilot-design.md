# Impossible Pooling Pilot — Design

**Date:** 2026-04-23
**Scope:** methods-triage pilot inside the shipped `impossible-ma` v0.1.1 repo
**Status:** design approved by user, ready for implementation plan

## Context

`ImpossibleMA` v0.1.1 ships a **Possibility Envelope** primitive bound to three meta-analytic impossibilities: `k1`, `missing_se`, `adversarial`. Four additional flavours of "impossible pooling" deserve triage before any of them earn a full build:

- **A — Disconnected NMA**: two treatment bubbles with no shared comparator.
- **B — Extreme heterogeneity**: τ² swamps the effect; classical point estimate is arithmetic but meaningless.
- **C — Cross-framing**: same construct reported under continuous / responder / ordinal framings.
- **D — Era-collision**: trials from eras with incomparable standard-of-care.

This design pilots all four inside `experiments/` so the winner can be promoted to a full sibling build later. Shipped code in `src/impossible_ma/` is not touched.

## Non-goals (explicit)

- No R parity.
- No hypothesis property tests.
- No real data — synthetic fixtures only.
- No UI / HTML.
- No shipped-API bump: v0.1.1 stays v0.1.1.
- No paper drafts, no TruthCert HMAC signing, no GitHub Pages update.
- `PilotEnvelope.to_possibility_envelope()` is a marker that raises `NotImplementedError` — promotion happens in a follow-up project, not here.

## Directory layout

All new code under `C:\Models\ImpossibleMA\experiments\`:

```
experiments/
├── README.md                 # "pilot, not shipped" — scope, non-goals, promotion-readiness scores
├── pilot_envelope.py         # shared PilotEnvelope dataclass
├── disconnected_nma.py       # flavour A
├── extreme_het.py            # flavour B
├── cross_framing.py          # flavour C
├── era_collision.py          # flavour D
├── compare.py                # runs all four, emits comparison.md
├── comparison.md             # output artifact
├── fixtures/
│   ├── disconnected_nma.json
│   ├── extreme_het.json
│   ├── cross_framing.json
│   └── era_collision.json
└── tests/
    ├── test_pilot_envelope.py
    ├── test_disconnected_nma.py
    ├── test_extreme_het.py
    ├── test_cross_framing.py
    ├── test_era_collision.py
    └── test_compare.py
```

One change to `pyproject.toml`: extend `[tool.pytest.ini_options].testpaths` from `["tests"]` to `["tests", "experiments/tests"]`. No other shipped files change.

## Shared type: `PilotEnvelope`

Mirrors `src/impossible_ma/envelope.py::PossibilityEnvelope` field-for-field with three deliberate diffs:

| Field | Shipped `PossibilityEnvelope` | `PilotEnvelope` |
|---|---|---|
| `case` | `Literal["k1","missing_se","adversarial"]` | `str` (free-form) |
| `flavour` | *(not present)* | `Literal["disconnected_nma","extreme_het","cross_framing","era_collision"]` |
| `upper` | finite `float` | `float`, `math.inf` allowed |

Shared invariants (same as shipped):
- `lower <= upper`
- If `point is not None`, then `lower <= point <= upper`
- `min_info` is a non-empty string

New invariant: **if `upper == math.inf` then `"unbounded"` must appear in `min_info`**. This forces every pilot to name its failure mode when it can't bound the envelope.

Adapter:
```python
def to_possibility_envelope(self) -> PossibilityEnvelope:
    raise NotImplementedError(
        f"promotion requires adding {self.flavour!r} to the Literal "
        f"in src/impossible_ma/envelope.py and porting this pilot to src/"
    )
```

## Pilot A — Disconnected NMA

**Intent:** emit an envelope for a cross-bubble contrast when no trial joins the bubbles.

**Input shape** (fixture JSON):
```json
{
  "bubble_1": {
    "studies": [{"id": "s1", "treat_a": "A", "treat_b": "B", "effect": -0.4, "se": 0.15}],
    "anchor_treatment": "A"
  },
  "bubble_2": {
    "studies": [...],
    "anchor_treatment": "C"
  },
  "bridging": {"delta_log_odds": 0.3},
  "target_contrast": ["A", "C"]
}
```

**Math:**
- REML pool within each bubble → `d̂₁` with `var₁`, `d̂₂` with `var₂`.
- Indirect contrast: `d_AC = d̂₁ + anchor_gap − d̂₂`, where `anchor_gap ∈ [−δ, +δ]`.
- Grid `anchor_gap` on 21 equally-spaced points; at each point compute the 95% CI; envelope is the union.
- `point = classical indirect estimate` iff `δ == 0`, else `None`.
- `k=1` bubble: use the single study's `effect` / `se²` as the bubble's `d̂` / `var` directly (no pool). `k=0` bubble raises `ValueError`.

**Stress cases:** `δ=0` (matches classical indirect, `tight`), `δ=1.0` (`normal`), `δ=∞` (`unbounded`, `upper=inf`, `min_info` must contain `"unbounded"`), empty bubble → `ValueError`.

## Pilot B — Extreme heterogeneity (honest anti-pooler)

**Intent:** refuse to emit a point estimate when τ² dominates.

**Input shape:**
```json
{
  "studies": [{"id": "s1", "effect": -0.1, "se": 0.05}, ...],
  "thresholds": {"i2_refuse_point": 0.80, "tau_ratio_refuse": 2.0}
}
```

**Math:**
- Compute DL τ̂² (diagnostic use only — `advanced-stats.md` permits this); derive I² via Higgins.
- Refusal rule: `I² >= i2_refuse_point` OR `τ̂ / |δ̂_FE| >= tau_ratio_refuse`.
- If refused: `point=None`, `lower = min(eᵢ − 1.96·seᵢ)`, `upper = max(eᵢ + 1.96·seᵢ)`, `min_info = "refused: I²=…, study-level envelope"`.
- Else: REML random-effects pool → standard point + 95% CI.

**Stress cases:** I²≈0 (`tight` — classical pool), I²=99% (`normal` — refuses), `k<3` → `ValueError` pointing at `impossible_ma.kone`.

## Pilot C — Cross-framing

**Intent:** pool continuous + responder + ordinal-framed studies into a shared latent SMD under conversion uncertainty.

**Input shape:**
```json
{
  "studies": [
    {"id": "s1", "frame": "continuous", "mean_diff": -3.2, "pooled_sd": 12.4, "n1": 100, "n2": 100},
    {"id": "s2", "frame": "responder", "p_ctrl": 0.30, "p_trt": 0.42, "n1": 80, "n2": 80},
    {"id": "s3", "frame": "ordinal_probit", "log_or": 0.35, "se": 0.12}
  ],
  "conversion_uncertainty": {"continuous_sd_cv": 0.10, "responder_threshold_sd_cv": 0.20}
}
```

**Math:**
- `continuous` → Hedges' g, standard variance.
- `responder` → Hasselblad-Hedges probit: `SMD = Φ⁻¹(p_trt) − Φ⁻¹(p_ctrl)`, delta-method variance, widened by `responder_threshold_sd_cv`.
- `ordinal_probit` from log-OR → `SMD ≈ log(OR) · √3/π` (≈ 0.5513 — **not** √(3/π); `lessons.md` rule), widened by same CV mechanism.
- REML random-effects pool on converted SMDs.
- Envelope: `pooled ± 1.96 · SE`, where `SE` is inflated by the conversion-uncertainty terms (added in quadrature to each study's variance before pooling).
- `point = pooled SMD` — bridging is principled, not just bounds, so a point is honest here.
- `conversion_uncertainty` defaults when missing: `continuous_sd_cv = 0.05`, `responder_threshold_sd_cv = 0.10`. Defaults applied are logged in the envelope's `assumptions` dict.

**Stress cases:** all-continuous (`tight` — matches classical SMD meta-analysis), all-responder (`tight` — matches probit pool), conflicting-signs mixed set (`normal` — wide envelope, high I²), unknown `frame` → `ValueError` listing valid values.

## Pilot D — Era-collision

**Intent:** pool trials from eras with different standard-of-care via a bridging parameter on the control-arm rate ratio.

**Input shape:**
```json
{
  "studies": [
    {"id": "s1", "era": 1, "log_hr": -0.25, "se": 0.08, "control_rate_per_year": 0.15},
    {"id": "s2", "era": 2, "log_hr": -0.18, "se": 0.09, "control_rate_per_year": 0.06}
  ],
  "bridging": {"beta_range": [-0.5, 0.5]}
}
```

**Math:**
- Era-reference control rate = arithmetic mean of `control_rate_per_year` across era-1 studies. For each era-2 study, `rate_ratio_era1_over_era2 = era1_ref_rate / study.control_rate_per_year`.
- For β in 21-point grid over `[β_lo, β_hi]`: adjust era-2 studies' log-HR via `log_hr_adj = log_hr + β · log(rate_ratio_era1_over_era2)`; era-1 studies unchanged.
- At each β: REML RE pool, 95% CI.
- `lower = min` over β of `pooled − 1.96·SE`; `upper = max` over β of `pooled + 1.96·SE`.
- `point = pool at β=0` iff `0 ∈ [β_lo, β_hi]`, else `None`.

**Stress cases:** `β_lo=β_hi=0` (`tight` — classical RE pool), `β ∈ [−1,1]` (`normal` — wide), all-one-era fixture (bridging inapplicable → classical pool, note in `assumptions`), missing `era` label → `ValueError`.

## Fixtures

Each JSON file has **three named cases**:

| Case key | Purpose | Expected outcome |
|---|---|---|
| `normal` | realistic inputs | bounded envelope, reasonable width |
| `tight` | degenerate params that collapse to classical (δ=0 / I²≈0 / all-one-frame / β=0) | envelope ≈ classical point ± classical CI (within ~5%). "Classical" = the same pool method with bridging/refusal off: REML RE pool for all four pilots. |
| `unbounded` | pathological params (δ=inf / I²=99% / conflicting frames / β∈[−10,10]) | `upper=math.inf` with `"unbounded"` in `min_info`, OR controlled `ValueError` |

Total: 12 fixture cases across 4 files.

## Compare harness

`compare.py` imports each pilot's `run(case_dict) -> PilotEnvelope`, runs all four against their `normal` case, writes `comparison.md`:

**Table 1 — normal-case comparison:**

| flavour | lower | upper | width | point | bounded? | bridging | min_info (truncated) |
|---|---|---|---|---|---|---|---|

**Table 2 — degenerate-case behaviour:**

| flavour | `tight` collapses to classical? | `unbounded` flagged correctly? | notes |
|---|---|---|---|

Output file committed; regenerated any time a pilot's math changes.

## Tests (~24 total)

- `test_pilot_envelope.py` (6): validation invariants mirror shipped `PossibilityEnvelope`; `upper=inf` without `"unbounded"` in `min_info` raises; `to_possibility_envelope()` raises `NotImplementedError`.
- `test_{flavour}.py` × 4 (4 tests each = 16): `test_normal_bounded`, `test_tight_matches_classical` (within ~5% of classical sanity-check), `test_unbounded_flagged`, one pilot-specific guard (e.g. `test_k_lt_3_raises` for B, `test_unknown_frame_raises` for C).
- `test_compare.py` (2): runs the harness on a tmpdir, asserts `comparison.md` has 4 flavour rows and both tables.

No R parity. No hypothesis property tests. (Profile 1, agreed.)

## Error handling

- Schema violation (missing/wrong-typed input field) → `ValueError` naming the exact field.
- Unbounded envelope is **not an error** — it's a valid result, encoded via `upper=math.inf` + `"unbounded"` in `min_info`.
- Missing optional bridging param → use documented default, record in `assumptions` dict, never silent.
- Pilot B `k<3` → `ValueError` with pointer: *"use `impossible_ma.kone` for k=1 or collect more studies"*.
- Pilot C unknown `frame` string → `ValueError` listing valid values.
- No silent failures, no fallback-that-drops-information patterns.

## "Done" definition

1. Four pilots' `normal` fixtures produce a valid bounded `PilotEnvelope`.
2. Four `tight` fixtures → envelope collapses to within ~5% of the classical sanity-check for that flavour.
3. Four `unbounded` fixtures → labelled `upper=math.inf` or controlled `ValueError`.
4. ~22 tests green (`pytest experiments/tests/`).
5. `comparison.md` committed.
6. `experiments/README.md` with a promotion-readiness score (1-5) + one-line justification per flavour.
7. Single commit on `master` of `C:\Models\ImpossibleMA\`. No tag, no release, no GitHub Pages.

## Scope / time estimate

Closed-form pools (scipy only, no statsmodels REML per grid point) → ~1 session.
If pilots A and D use full statsmodels REML at each of 21 grid points → ~2 sessions.

**Pilot default: closed-form route.** The point of a pilot is triage; the winner gets upgraded to REML-per-grid in the follow-up build, not here.

## Implementation plan

Generated separately via the `superpowers:writing-plans` skill after user review of this spec.
