# Plan 4 Review — ImpossibleMA Ship (partial)

## Summary

ImpossibleMA shipped publicly as of 2026-04-16. GitHub repo public, Pages live, v0.1.0 release published. **INDEX.md append (Task 5) deferred** due to pre-existing systemic registry drift that must be resolved in a dedicated session. Public artefacts are complete and unblock paper submissions; registry catches up later.

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
| `LICENSE` | `106d907` | MIT, `{{AUTHOR_1_NAME}}` placeholder |
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

1. Replace `{{AUTHOR_*}}` placeholders in `LICENSE`, `CITATION.cff`, and `paper/AUTHORS.md` before formal publication.
2. Synthesis submission for the three papers; Synthesis mints the DOI; find-replace `ZENODO_DOI_PENDING` across `paper/refs.bib` and `paper/f1000.md` once assigned.
3. Optional: `index.html` symlink/copy at repo root so the Pages URL resolves without the `/impossible-ma.html` suffix.
4. v0.1.1: figure-extraction route for missing_se, auto-MeSH for kone.

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
