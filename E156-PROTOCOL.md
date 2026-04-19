# E156 Protocol — `impossible-ma`

This repository is the source code and dashboard backing an E156 micro-paper on the [E156 Student Board](https://mahmood726-cyber.github.io/e156/students.html).

---

## `[484]` ImpossibleMA: Bounded Synthesis of Cochrane Meta-Analyses Declared Unpoolable

**Type:** methods  |  ESTIMAND: Possibility Envelope on log-effect scale  
**Data:** 6,229 MetaAudit meta-analyses (68,519 audit rows across 11 diagnostic modules); 444 flagged CRITICAL for prediction_gap converted to bounded adversarial envelopes.

### 156-word body

Cochrane meta-analyses with prediction intervals crossing the null are conventionally deemed to have no defensible pooled estimate, leaving guideline panels with narrative synthesis. We screened 6,229 meta-analyses in the MetaAudit corpus (68,519 audit rows, 11 diagnostic modules) for any module flagged CRITICAL. The Possibility Envelope — `(lower, upper, point|None, min_info, assumptions)` — is computed by an adversarial engine enumerating inclusion-rule combinations and reporting REML+HKSJ extremes. 444 of 6,229 meta-analyses (7.13%) carried at least one CRITICAL flag; the priority classifier converted all 444 to bounded adversarial envelopes via `prediction_gap`, zero unclassified. REML matches `metafor::rma` to 1e-4; envelope monotonicity and full-data containment are property-tested across 23 inputs; 88 automated tests gate every commit. The envelope bounds defensible pooled effects under stated inclusion rules; one named datum (e.g., a pre-registered protocol) collapses it to a point. v1 covers k=1, missing-SE, and adversarial cases; figure-extraction, incommensurable outcomes, and per-MA runs are deferred; only `prediction_gap` fires CRITICAL in the current snapshot.

### Submission metadata

```
Corresponding author: Mahmood Ahmad <mahmood.ahmad2@nhs.net>
ORCID: 0000-0001-9107-3704
Affiliation: Tahir Heart Institute, Rabwah, Pakistan

Links:
  Code:      https://github.com/mahmood726-cyber/impossible-ma
  Protocol:  https://github.com/mahmood726-cyber/impossible-ma/blob/main/E156-PROTOCOL.md
  Dashboard: https://mahmood726-cyber.github.io/impossible-ma/

References (topic pack: meta-analytic priors / robust pooling):
  1. Schmidli H, Gsteiger S, Roychoudhury S, O'Hagan A, Spiegelhalter D, Neuenschwander B. 2014. Robust meta-analytic-predictive priors in clinical trials with historical control information. Biometrics. 70(4):1023-1032. doi:10.1111/biom.12242
  2. Viechtbauer W. 2010. Conducting meta-analyses in R with the metafor package. J Stat Softw. 36(3):1-48. doi:10.18637/jss.v036.i03

Data availability: No patient-level data used. Analysis derived exclusively
  from publicly available aggregate records. All source identifiers are in
  the protocol document linked above.

Ethics: Not required. Study uses only publicly available aggregate data; no
  human participants; no patient-identifiable information; no individual-
  participant data. No institutional review board approval sought or required
  under standard research-ethics guidelines for secondary methodological
  research on published literature.

Funding: None.

Competing interests: MA serves on the editorial board of Synthēsis (the
  target journal); MA had no role in editorial decisions on this
  manuscript, which was handled by an independent editor of the journal.

Author contributions (CRediT):
  [STUDENT REWRITER, first author] — Writing – original draft, Writing –
    review & editing, Validation.
  [SUPERVISING FACULTY, last/senior author] — Supervision, Validation,
    Writing – review & editing.
  Mahmood Ahmad (middle author, NOT first or last) — Conceptualization,
    Methodology, Software, Data curation, Formal analysis, Resources.

AI disclosure: Computational tooling (including AI-assisted coding via
  Claude Code [Anthropic]) was used to develop analysis scripts and assist
  with data extraction. The final manuscript was human-written, reviewed,
  and approved by the author; the submitted text is not AI-generated. All
  quantitative claims were verified against source data; cross-validation
  was performed where applicable. The author retains full responsibility for
  the final content.

Preprint: Not preprinted.

Reporting checklist: PRISMA 2020 (methods-paper variant — reports on review corpus).

Target journal: ◆ Synthēsis (https://www.synthesis-medicine.org/index.php/journal)
  Section: Methods Note — submit the 156-word E156 body verbatim as the main text.
  The journal caps main text at ≤400 words; E156's 156-word, 7-sentence
  contract sits well inside that ceiling. Do NOT pad to 400 — the
  micro-paper length is the point of the format.

Manuscript license: CC-BY-4.0.
Code license: MIT.

SUBMITTED: [ ]
```


---

_Auto-generated from the workbook by `C:/E156/scripts/create_missing_protocols.py`. If something is wrong, edit `rewrite-workbook.txt` and re-run the script — it will overwrite this file via the GitHub API._