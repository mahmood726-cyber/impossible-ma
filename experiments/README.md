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
| disconnected_nma | ✓ Promoted to v0.2.0 | See `src/impossible_ma/disconnected_nma.py`. Ported with REML bubble-pool upgrade (spec-faithful). |
| extreme_het | ✓ Promoted to v0.2.0 | See `src/impossible_ma/extreme_het.py`. Refusal discipline shipped unchanged from pilot. |
| cross_framing | 3 | Conversion math is correct (sqrt(3)/pi constant, probit conversion) and the normal case pools sensibly, but the unbounded fixture with genuinely conflicting-sign framings and 50% CV produces only a "bounded (wide)" envelope rather than triggering refusal — a full-build promotion needs an explicit conflict-severity gate. |
| era_collision | 3 | Grid enumeration over β works and the normal/tight cases are correct, but the unbounded stress test only asserts width>1.0 (a weak bar given β∈[−5,5] with a 4:1 rate ratio), and the envelope width is not verified to scale proportionally with β range — a full-build promotion should tighten the unbounded contract and add REML per grid point. |
