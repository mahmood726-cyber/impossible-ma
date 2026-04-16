# Plan 3 Review — ImpossibleMA Manuscripts

## Summary

Three drafts shipped:

| Paper | File | Words | Target | Status |
|-------|------|-------|--------|--------|
| E156 micro | `paper/e156.md` | 156 exact | ≤156 | ✅ at limit |
| F1000 software | `paper/f1000.md` | ~1,228 | ~2,500 | ✅ structurally complete; shorter than target |
| BMJ Methods | `paper/bmj_methods.md` | ~1,744 | ~3,500 | ✅ structurally complete; shorter than target |

All three papers anchor-verified against `scripts/headline_output.json` (`n_ma_total=6229`, `denominator_critical=444`). No stray `{{...}}` placeholders in any paper body. E156 appended to `C:\E156\rewrite-workbook.txt` as entry `[484/484] impossible-ma` with SHA-256 proof that no prior entry was touched.

## Files added (Plan 3)

| File | Commit | Role |
|------|--------|------|
| `paper/AUTHORS.md` | `f4418eb` | Author placeholders (`{{AUTHOR_*}}`) |
| `paper/refs.bib` | `f4418eb` | Shared BibTeX (12 entries) |
| `paper/figures/kone_rare_hf.svg` | `bd5ff0c` | k=1 density figure (13 KB) |
| `paper/figures/missing_se_multi.svg` | `bd5ff0c` | missing_se route comparison (9 KB) |
| `paper/figures/adversarial_pcsk9.svg` | `bd5ff0c` | adversarial pool histogram (17 KB) |
| `scripts/export_figures.py` | `bd5ff0c` | Automated figure exporter via Pyodide |
| `paper/e156.md` | `967962b` | 7-sentence micro-paper (156 words exact) |
| `paper/f1000.md` | `f44a074` | F1000 software paper |
| `paper/bmj_methods.md` | `b69be90` | BMJ Methods framework paper |

Plus E156 workbook append (outside this repo, at `C:\E156\rewrite-workbook.txt` entry 484).

## Verification gates passed

- All anchor numbers (444, 6,229, 7.13%, 68,519 audit rows, 88 tests) trace to `scripts/headline_output.json`.
- E156 word count: **156 exact** (at limit).
- E156 structural: 7 sentences labelled S1–S7.
- F1000: all 5 preempted reviewer Q markers present (`**Q1`–`**Q5`).
- BMJ: all 5 Discussion subsections present (5.1 Envelope ≠ estimator, 5.2 Boundary, 5.3 Prior work, 5.4 Research agenda, 5.5 Clinical).
- BMJ: formal three-invariants definition present (Ordering, Point membership, Minimal collapse).
- No banned marketing words (Global, Complete, Integrated). "Full borrowing" exempted as technical term (MAP weight = 1).
- No invented author names, affiliations, ORCIDs, or DOIs — all deferred to `AUTHORS.md` placeholders or `ZENODO_DOI_PENDING`.
- Cross-paper numerical consistency verified via a single Python check that loops all three papers against `headline_output.json`.

## Known observations (not blockers)

1. **F1000 and BMJ are shorter than target word counts** (1,228 / 1,744 vs ~2,500 / ~3,500). The drafts cover every required structural element; the gap is in expository depth, not content. Expansion targets per the Task 6 subagent:
   - F1000: expand Introduction (+background on impossibility classes), Use Cases (+numerical walkthrough per dataset), Discussion (+extended comparison with prior tools).
   - BMJ: expand Introduction (+burden of narrative synthesis), §3 worked examples (+per-case commentary), §4 validation (+module-level sensitivity), Discussion §5.3 / §5.4 (+extended prior-work positioning and research agenda).
   - Recommend this expansion as an editorial pass with domain-expert input rather than automation, to avoid inflating the anchor table's numbers.

2. **E156 at exactly 156 words** means zero slack for future phrasing tweaks. Any rewording must retain length — add a word, remove a word.

3. **Figures are Plotly SVG exports** of the HTML app's built-in datasets. If the HTML app changes, re-run `python scripts/export_figures.py` to refresh.

## What Mahmood does next

- Replace `{{AUTHOR_*}}` placeholders in `paper/AUTHORS.md` before submission.
- Replace `ZENODO_DOI_PENDING` strings after Plan 4 mints the actual DOI.
- E156 workbook entry 484 at `C:\E156\rewrite-workbook.txt` is `SUBMITTED: [ ]` — toggle to `[x]` when actually submitted.
- F1000 and BMJ drafts ready for editorial expansion pass and venue-specific formatting.
- Target submissions per `paper/e156.md`'s entry metadata: Synthēsis (E156 section: Methods Note).

## Plan 3 commits

1. `f4418eb` feat: AUTHORS.md placeholder block + refs.bib shared citations
2. `bd5ff0c` feat: export 3 manuscript figures from HTML app via Pyodide
3. `967962b` feat: E156 micro-paper draft
4. (workbook-repo commit — not in this repo)
5. `f44a074` feat: F1000 software paper draft
6. `b69be90` feat: BMJ Methods framework paper draft
7. (this REVIEW commit)

## Next: Plan 4 (GitHub Pages + Zenodo DOI)
