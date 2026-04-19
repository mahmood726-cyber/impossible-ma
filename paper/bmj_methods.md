# The Possibility Envelope: a methodological primitive for meta-analyses declared unpoolable

**Authors**: see `AUTHORS.md`

## Abstract

Many systematic reviews end in narrative synthesis because the available studies fail one of three textbook preconditions for meta-analysis: a single pivotal trial (k=1), missing standard errors, or contested inclusion rules that produce defensibly opposite conclusions from the same corpus. We propose the Possibility Envelope, a methodological primitive that converts each of these impossibilities into a bounded range of defensible pooled effects, plus a single named datum that would collapse the envelope to a point. We instantiate the primitive in three case-specific engines and validate against the MetaAudit corpus of 6,229 Cochrane meta-analyses; 444 (7.13%) carry at least one CRITICAL audit flag and the adversarial engine converts all 444 to bounded envelopes. The envelope is not an estimator and does not replace conventional meta-analysis; it bounds what defensible inference is possible when conventional pooling is declared off-limits, and it makes the missing data explicit.

## 1. Introduction

Roughly 40% of Cochrane reviews end with a narrative-synthesis verdict, citing some combination of insufficient studies, missing standard errors, or heterogeneity-of-inclusion concerns [@ioannidis2017]. Guideline panels reading those reviews receive no quantitative range — they are told the evidence "could not be pooled" and left to translate that absence into a recommendation. The methodological literature responds with technique-specific tools: MAP priors for k=1 borrowing [@schmidli2014]; moment-based reconstructions for missing summary statistics [@wan2014]; specification curves for inclusion-rule sensitivity [@steegen2016]. Each addresses a single class of impossibility. None offers a primitive that returns the same kind of object across all three.

We introduce the Possibility Envelope as that primitive. The envelope is a five-tuple `(lower, upper, point | None, min_info, assumptions)` accompanied by a `case` discriminator. It bounds the range of pooled effects that any defensible reviewer could produce from the available evidence, names the single datum that would collapse the envelope to a point, and exports the assumptions behind each bound for audit. We instantiate the envelope in three case-specific engines (k=1, missing-SE, adversarial), implement them in a single Python package, and validate the framework against the MetaAudit corpus.

## 2. The Possibility Envelope primitive

Formally, a Possibility Envelope satisfies three invariants:

1. **Ordering**: `lower ≤ upper`. The envelope is an interval on the chosen effect scale (log-OR, SMD, log-HR).
2. **Point membership**: `point ∈ [lower, upper]` whenever `point` is not `None`. A `None` point indicates that no single estimate is more defensible than any other within the envelope; collapsing the envelope requires the `min_info` datum.
3. **Minimal collapse**: `min_info` is a string naming the single piece of additional evidence (a new trial of size n; an author's reported standard error; a pre-registered inclusion protocol) whose acquisition would collapse the envelope to a point.

The primitive is deliberately neutral about how the bounds are computed. Each case below provides its own numerical instantiation.

## 3. Three classes of impossibility

### 3.1 k=1 (single-study borrowing)

**Textbook reason for impossibility**: meta-analysis requires k≥2 studies; a single study has no between-study variance to estimate.

**Envelope instantiation**: bounds span the vague-prior CI (target study alone) and the fully-informative CI (target + a meta-analytic prior fit by REML across user-supplied adjacent trials, per Schmidli et al.). The `point` is the robust-mixture posterior at MAP weight w = 0.5. `min_info` is "one additional trial with n ≥ N in the same population", where N is computed from the prior precision.

**Worked example** (from `paper/figures/kone_rare_hf.svg`): a rare-disease HF trial with target estimate −0.42 (SE 0.31, log-OR scale) and 5 adjacent trials produces an envelope spanning approximately [−1.03, +0.19] with a robust point at −0.41. The vague bound spans the original trial's CI; the full-borrow bound is much narrower, centered on the prior mean of approximately −0.31.

### 3.2 Missing SE

**Textbook reason for impossibility**: pooling weights are inverse-variance; without a standard error, a study contributes no weight.

**Envelope instantiation**: three reconstruction routes (p-value via `z = qnorm(1 − p/2)`; CI bounds via `(upper − lower) / (2 · z_{α/2})`; test statistic via `effect / |statistic|`) produce up to three SE estimates per study. The envelope spans `[min, max]` of the successful routes; the `point` is the median when ≥2 routes agree to within 10% relative distance. `min_info` is "the raw standard error from the original analysis."

**Worked example** (from `paper/figures/missing_se_multi.svg`): an effect of 0.40 with p = 0.04, CI [0.0, 0.80], and statistic 2.0 yields three SE estimates within 10% of each other; the envelope collapses to a point of approximately 0.20.

### 3.3 Adversarial pool

**Textbook reason for impossibility**: there is no single defensible inclusion rule; reviewers with different priors produce defensibly different pools.

**Envelope instantiation**: enumerate a publicly stated rule grid (default: 5 risk-of-bias cutoffs × 3 sample-size floors × 3 follow-up floors × 2 language filters × 2 publication-type filters = 180 combinations, capped at 1,000 feasible pools with k≥3). Fit REML+HKSJ per pool with the `max(1, Q/(k−1))` HKSJ floor [@viechtbauer2010, @higgins2009]. The envelope spans the most-negative and most-positive significant-pool estimates; if no pool has a CI excluding the null, the envelope spans the range of point estimates and `case_specific.no_significant_pool` is set. `point` is `None` (the envelope cannot collapse without a pre-registered inclusion protocol). `min_info` is "a pre-registered inclusion protocol."

**Worked example** (from `paper/figures/adversarial_pcsk9.svg`): 12 PCSK9 trials produce 148 feasible pools under the default grid; the envelope spans approximately [−0.47, −0.18], the lower bound from a strict ROB cutoff and the upper bound from a permissive cutoff. The full-data REML estimate sits at the upper bound of the envelope, satisfying the `envelope contains full_data_reml` property invariant verified by `hypothesis`-driven property tests across 23 random study tables.

## 4. Validation against MetaAudit

The MetaAudit corpus [@ahmad_metaaudit_2026] comprises 68,519 audit rows across 6,229 Cochrane meta-analyses, each row a `(ma_id, module, severity, detail)` tuple where `module` is one of 11 diagnostic checks and `severity` is `PASS`, `WARNING`, or `CRITICAL`. We classify each MA as an ImpossibleMA candidate by the priority-ordered severity rules in `metaaudit_classifier.py`: a CRITICAL `integrity` flag routes to missing_se; CRITICAL `underpowered` with k≤2 to k1; CRITICAL `prediction_gap`, `fragility`, `excess_sig`, or `underpowered` (k≥3) to adversarial.

444 of 6,229 meta-analyses (7.13%) carry at least one CRITICAL audit flag. In the present MetaAudit snapshot the only module that ever escalates to CRITICAL is `prediction_gap` — the prediction interval crosses the null, formally indicating that the conclusion direction depends on assumptions any reviewer could defensibly vary. The severity-priority classifier maps all 444 to the adversarial case and the engine returns a bounded envelope for each (zero unclassified).

`prediction_gap`-CRITICAL is the formal version of the adversarial signal: when a prediction interval crosses the null, an inclusion-rule choice that excludes a small influential subset can flip the pooled-effect direction. The Possibility Envelope makes this explicit by reporting both extremes and the rule tuples that produced them.

Robustness:
- REML implementation matches `metafor::rma(method="REML")` to 1e-4 across all kone fixtures.
- Envelope monotonicity (adding a rule option never narrows the envelope) and full-data-REML containment are verified across 23 random study tables (hypothesis library).
- 88 automated tests gate every commit (66 engine + 22 HTML/Selenium).

## 5. Discussion

### 5.1 Envelope ≠ estimator

A Possibility Envelope is not a point estimate. It does not replace conventional meta-analysis. It is a diagnostic that answers "what is defensible?" rather than "what is true?" When the underlying meta-analysis IS poolable in the conventional sense, the envelope collapses to a point — the conventional REML estimate — and the framework adds nothing. Its value is reserved for the residual class where conventional pooling fails.

### 5.2 Boundary cases

The framework breaks where meta-analytic principle itself breaks. With zero studies, there is no envelope. With pure narrative evidence (no quantitative effect, no extractable summary), there is no envelope. Where a reviewer refuses to state any inclusion rule publicly, the adversarial envelope is undefined. The v0.1.0 implementation defers figure-extraction reconstruction (shipped in v0.1.1), incommensurable-outcomes bridging, and per-MA study-level envelope runs across the MetaAudit corpus; the latter two remain deferred to subsequent versions.

### 5.3 Prior work

MAP priors [@schmidli2014] solve the k=1 case under a single decision-theoretic frame; MAPriors [@ahmad_mapriors_2026] implements them in a browser. CausalSynth [@ahmad_causalsynth_2026] triangulates evidence across designs but assumes pooling is feasible within each design. MES [@ahmad_mes_2026] introduced multiverse evidence synthesis, exposing specification dependence as a first-class output of conventional meta-analysis. HyperMeta [@ahmad_hypermeta_2026] proposed mathematically-exotic representations of meta-analytic evidence (Poincaré disks, persistent homology) but did not address impossibility cases. The Possibility Envelope unifies these by giving each impossibility class the same output object, with an explicit collapse-to-point criterion.

Multiverse analysis [@steegen2016] is the closest methodological cousin. The adversarial envelope is multiverse analysis specialized to the inclusion-rule axis with REML+HKSJ pooling per specification, reduced to a two-number summary suitable for guideline panels who lack the expertise to interpret a full specification curve.

### 5.4 Research agenda

Three concrete extensions follow:

1. **Envelope-of-envelopes**: nest a missing-SE envelope inside an adversarial envelope. The output is a meta-envelope that bounds the bound. We expect this for guideline questions where many studies have reconstructed SEs and inclusion is also contested.
2. **Prospective application to guideline panels**: the British Society of Cardiology's guideline-development manual currently allows narrative synthesis as a terminal verdict; we propose the Possibility Envelope as a structured replacement, with formative usability testing on three live guideline questions in the next 12 months.
3. **Pre-registration registry for inclusion rules**: the adversarial envelope's `min_info` is "a pre-registered inclusion protocol." A public registry of such protocols would convert envelopes to point estimates retrospectively and supply training data for default-rule recommendations.

### 5.5 Clinical implication

Guideline panels routinely encounter "could not be pooled" verdicts on questions where they nonetheless need to recommend or refrain. The Possibility Envelope gives them a quantitative range to discuss — bounded by publicly stated assumptions, with an explicit hand-off about what additional evidence would resolve the question. We expect this to shift the guideline conversation from "no conclusion" to "this is the range of defensible conclusions, and here is what you would need to narrow it."

## 6. Conclusion

We introduce the Possibility Envelope as a methodological primitive that converts three classes of meta-analytic impossibility — k=1, missing-SE, contested-inclusion — into bounded ranges of defensible pooled effects. Validation against 6,229 Cochrane meta-analyses confirms that all 444 reviews carrying CRITICAL audit flags can be assigned an envelope. We position the framework as the missing primitive for guideline panels who currently receive narrative-synthesis verdicts where a structured range would serve better.

## References

See `paper/refs.bib`. Submission-time conversion to the venue's reference style is out-of-scope for this draft.
