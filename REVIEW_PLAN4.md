# Plan 4 Review — ImpossibleMA Ship

## Summary

ImpossibleMA shipped publicly 2026-04-16. GitHub repo public, Pages live, v0.1.0 release published. Cleanup follow-ups closed 2026-04-18: author placeholders filled, Zenodo refs replaced with Crossref policy, `index.html` redirect live at Pages root, INDEX.md entry present and DOI line corrected, registry reconciler now green. Remaining open items: user-side paper submissions (x3) and v0.1.1 feature work.

## Public URLs (all live)

- Repo: https://github.com/mahmood726-cyber/impossible-ma
- Pages: https://mahmood726-cyber.github.io/impossible-ma/impossible-ma.html
- Release: https://github.com/mahmood726-cyber/impossible-ma/releases/tag/v0.1.0

## Verification gates

- ✅ Pages URL returns 200 for `impossible-ma.html` (1s response, Pages was already cached)
- ✅ Repo is PUBLIC at `mahmood726-cyber/impossible-ma`, default branch `master`, pushed 2026-04-16T10:12Z
- ✅ v0.1.0 release published with source archives
- ⏸ `reconcile_counts.py` — **pre-existing FAIL, not caused by Plan 4**. See §Deferred below.

## Files added (Plan 4)

| File | Commit | Role |
|------|--------|------|
| `README.md` | `106d907` | Public landing page |
| `LICENSE` | `106d907` | MIT — author placeholder resolved to Mahmood Ahmad |
| `CITATION.cff` | `106d907` | Machine-readable citation metadata |
| `REVIEW_PLAN4.md` | (this commit) | This review |

## Plan 4 commits (local repo)

1. `106d907` docs: add README + MIT LICENSE + CITATION.cff for public ship
2. (this commit) docs: Plan 4 partial review

Remote-only actions (no local commits):
- `gh repo create mahmood726-cyber/impossible-ma --public`
- `git push -u origin master` (47 commits)
- `gh api .../pages` (enable Pages)
- `gh release create v0.1.0` (with release notes)

## Deferred — registry reconciliation (separate session required)

`reconcile_counts.py` reports pre-existing systemic drift:

- **201-project gap**: manifest has 468 projects; `INDEX.md` lists 267. Many manifest entries are not in the curated index.
- **2 MISSING paths**: `wb-data-lakehouse` and `who-data-lakehouse` are marked Active in the manifest but their directories don't exist on disk (any drive).
- **17-project workbook surplus**: `rewrite-workbook.txt` has 485 entries vs manifest's 468 — likely historical / submitted-separately entries.

None of this is caused by Plan 4. Per spec §3 and Task 0 Step 5, we did NOT append to INDEX.md to avoid masking the drift. The ImpossibleMA entry for INDEX.md is drafted and ready to paste during the registry session:

```markdown
### ImpossibleMA
- **Path**: `C:\Models\ImpossibleMA\`
- **Repo**: https://github.com/mahmood726-cyber/impossible-ma
- **Pages**: https://mahmood726-cyber.github.io/impossible-ma/
- **DOI**: pending Synthesis submission
- **Status**: Shipped 2026-04-16
- **Tests**: 88 (66 engine + 22 UI)
- **Papers**: E156 (workbook 484), F1000 draft, BMJ Methods draft
- **Headline**: 444 of 6,229 MetaAudit MAs with CRITICAL flags converted to bounded Possibility Envelopes
```

## Other deferred follow-ups

1. ✅ **Done 2026-04-18 (commit `bb1828d`)**: replaced `{{AUTHOR_*}}` placeholders in `LICENSE`, `CITATION.cff`, `paper/AUTHORS.md` with Mahmood Ahmad author block (Royal Free, ORCID 0009-0003-7781-4478). Funding "none". COI: editorial-board disclosure for Synthēsis submission.
2. **In progress — awaits user action**: submit the three papers. DOI policy updated 2026-04-18 — **Crossref**, not Zenodo (journals register via Crossref at publication). All `ZENODO_DOI_PENDING` scrubbed (`paper/refs.bib` x5, `paper/f1000.md` x2, `paper/AUTHORS.md` x1); replaced with Crossref notes.
3. ✅ **Done 2026-04-18 (commit `637a3f3`)**: `index.html` meta-refresh redirect at repo root. Pages verified live — <https://mahmood726-cyber.github.io/impossible-ma/> returns 200 and redirects to `impossible-ma.html`. Open Graph tags included for unfurls.
4. **Deferred — needs its own plan**: v0.1.1 figure-extraction route for missing_se + auto-MeSH for kone.

## Registry reconciliation (deferred §Deferred at write time — now resolved)

Re-ran `python C:\ProjectIndex\reconcile_counts.py` on 2026-04-18 — returns `[RESULT] OK`, exit 0. 0 missing paths, 0 broken shells, no stale text claims, no workbook denominator drift. The `wb-data-lakehouse` / `who-data-lakehouse` paths noted at Plan 4 write-time no longer fail the reconciler. INDEX.md entry for ImpossibleMA present at `C:\ProjectIndex\INDEX.md:1069` (DOI line corrected to Crossref on 2026-04-18).

## Combined project stats (Plans 1–4)

- **48 local commits** on master (47 pre-ship + Plan 4's README commit + this REVIEW)
- **88 automated tests** (66 engine + 22 Selenium), all passing
- **51 KB single-file HTML app** (Pyodide + wheel + Plotly)
- **3 manuscript drafts** (E156 at 156 words exact, F1000 ~1,228 words, BMJ Methods ~1,744 words)
- **3 SVG figures** from live HTML exports
- **444 / 6,229** MetaAudit headline anchor
- **R parity** at 1e-4 tolerance

## Session handoff

Future sessions can find this project via:
- `C:\Models\ImpossibleMA\` (local path, clean master at push time)
- https://github.com/mahmood726-cyber/impossible-ma (remote)
- https://mahmood726-cyber.github.io/impossible-ma/impossible-ma.html (public app)

The INDEX.md entry sits in this review file ready to paste once the registry hygiene session has closed the 201-gap and resolved the 2 missing paths.
