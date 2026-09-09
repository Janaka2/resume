---
name: weekly-brand-review
description: Proactive weekly maintenance of janaka.me - runs the site-health, brand-audit, SEO and market-trend agents in parallel, merges their findings into one prioritised report, applies the safe fixes (broken links, meta, i18n gaps, sitemap), and leaves a branch + summary for the rest. Use weekly (pair with /loop or /schedule) or before any release.
---

# Weekly brand review

This is the orchestrator. It delegates and then decides.

## 1. Gather (parallel)

Launch these agents in one message so they run concurrently:

- `site-health-checker` — full technical check
- `brand-auditor` — positioning and copy consistency
- `seo-optimizer` — meta audit only (no edits yet)
- `academy-curator` — scaffold and index integrity report
- `market-trend-analyst` — only if it has not run in the last 30 days (check `git log --grep="market pulse"`)

## 2. Merge

Combine findings into one table: `severity | area | file | fix | auto-fixable?`. Severity: **P1** broken links, missing includes, factual drift (years, titles, contact); **P2** missing meta / OG / canonical, i18n gaps, scaffold backlog; **P3** wording, keyword alignment, opportunities.

## 3. Fix what is safe

On a branch `chore/brand-review-YYYY-MM-DD`, apply autonomously:

- Broken internal links and include paths
- Missing pre-paint script / chrome on non-archived pages
- Missing title/description/canonical/og tags (using `seo-optimizer` wording)
- `sitemap.xml` and `robots.txt` regeneration
- i18n keys missing in DE (delegate to `i18n-translator`)
- Learning-log / nav / notes-index consistency (delegate to `academy-curator`)
- Up to five academy scaffolds (delegate to `content-writer`, oldest first)

Do **not** autonomously change: career facts, product claims, hero copy, the chatbot prompt, the topic rotation. Propose those.

## 4. Verify and report

Run `site-health-checker` again on the branch; it must report zero P1. Commit with message `Weekly brand review YYYY-MM-DD` and the standard trailers. Then write the report to `reports/brand-review-YYYY-MM-DD.md` on the same branch containing: counts before/after, what was fixed, the P2/P3 proposals with exact copy, the market signals of the month, and three content ideas. Push the branch and open a PR with `gh pr create` if `gh` is authenticated; otherwise leave the branch and say so.

Final message to the user: five lines max — health score, what changed, what needs a decision, PR link.
