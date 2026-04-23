# ImpossibleMA — Experiments (pilots, not shipped)

Four impossible-pooling flavours piloted as methods-triage for promotion to a
follow-up v0.2.x build. **Not part of the shipped `impossible-ma` API.**
`src/impossible_ma/` is untouched; promotion happens in a separate project,
not here.

Spec: `../docs/superpowers/specs/2026-04-23-impossible-pooling-pilot-design.md`
Plan: `../docs/superpowers/plans/2026-04-23-impossible-pooling-pilot.md`

## Run

```bash
pytest experiments/tests/              # ~27 tests
python -m experiments.compare          # regenerates experiments/comparison.md
```

## Non-goals

No R parity. No hypothesis property tests. No real data (synthetic fixtures
only). No UI. No shipped API bump. No TruthCert HMAC signing of
`PilotEnvelope`. See spec §Non-goals.

## Promotion-readiness scores (1-5)

Scored after reading `comparison.md`. 5 = ready to promote; 1 = pilot shows
the flavour needs rethinking.

| Flavour | Score | One-line justification |
|---|---|---|
| disconnected_nma | 4 | Normal width=1.168 with point correctly suppressed (δ>0), tight collapses to classical, unbounded correctly inf-flagged — only caveat is FE-within-bubbles rather than REML, which is acceptable for the pilot but must be upgraded in the follow-up build. |
| extreme_het | 5 | Refusal fires reliably at I²=0.98/tau_ratio=57.10, study-level envelope is the correct fallback, tight produces a pooled point, and thresholds are configurable — the methodological intent is fully realised. |
| cross_framing | 3 | Conversion math is correct (sqrt(3)/pi constant, probit conversion) and the normal case pools sensibly, but the unbounded fixture with genuinely conflicting-sign framings and 50% CV produces only a "bounded (wide)" envelope rather than triggering refusal — the follow-up build needs an explicit conflict-severity gate before promoting. |
| era_collision | 3 | Grid enumeration over β works and the normal/tight cases are correct, but the unbounded stress test only asserts width>1.0 (a weak bar given β∈[−5,5] with a 4:1 rate ratio), and the envelope width is not verified to scale proportionally with β range — the follow-up build should tighten the unbounded contract and add REML per grid point. |
