# Maintenance 2026-09-25

**Result:** PASS — all checks green before and after; only watchlist review dates changed, and five proposals are left for Janaka.

Run: local on-demand smoke test, focus `all`, as a sub-agent. The Agent tool was not used; I applied the quality-guardian
checklist myself. The working tree already held about 140 uncommitted changes from the site overhaul. I did not judge
or touch them.

## Checks
| Check | Before | After |
|---|---|---|
| `scripts/build.py --check` | derived files current (77 URLs sitemap, 70 index entries, 30 feed entries, 0 public files changed) | same |
| `scripts/validate-site.py` | OK, 77 pages; 0 FAIL, 8 WARN (meta descriptions over 160 chars) | same |
| JS tests (`node --test tests/js/*.test.mjs`) | 19/19 pass | 19/19 pass |
| Python tests (`unittest discover -s tests/python`) | 18/18 OK | 18/18 OK |
| External links (`maintenance-scan.py --links`) | 106 checked, 4 failing (all 403 = blocked, none gone) | not rechecked (no link changes) |
| Watchlist radar | 4 items due | 1 item due (`github-actions-versions`, janaka authority) |

## Changed (tiers A and B)
- `content/watchlist.json`: set `checked` to `2026-09-25` on three items (tier A):
  - `google-search-guidance`: official docs show no deprecation that affects us. See the Watchlist section for the evidence.
  - `llms-txt-format`: llmstxt.org now publishes v2, which is backward compatible. Our `render_llms()` output still conforms, so no code change was needed.
  - `products-live`: **reachability only.** All five URLs returned HTTP 200. I did not verify the copy or product status.

No tier B changes.

## Proposals for Janaka (tier C)
1. **GitHub Actions majors (low urgency).** v7 is current for all three actions: checkout v7.0.1 (2026-07-20),
   setup-python v7.0.0 (2026-07-20) and setup-node v7.0.0 (2026-07-14). The repo pins checkout@v4, setup-python@v5 and
   setup-node@v4.
   - None of the workflows uses an input that was removed or changed. setup-python v7 drops `pip-install`, setup-node
     v6 limits automatic caching to npm, and checkout v7 blocks fork-PR checkout only under
     `pull_request_target`/`workflow_run`. No workflow uses those inputs or triggers.
   - v5 and later need runner ≥ v2.327.1 (Node 24). GitHub-hosted runners meet that.
   - Proposed diff, applied the same way in `autonomous-maintenance.yml`, `site-checks.yml`,
     `daily_learning_generator.yml` and `daily_update.yml`:
   ```diff
   -      uses: actions/checkout@v4
   +      uses: actions/checkout@v7
   -      uses: actions/setup-python@v5
   +      uses: actions/setup-python@v7
   -      uses: actions/setup-node@v4
   +      uses: actions/setup-node@v7
   ```
   After the bump, trigger `site-checks` and one `workflow_dispatch` run. Then set `github-actions-versions.checked`.
   Source: https://github.com/actions/checkout/releases, https://github.com/actions/setup-python/releases,
   https://github.com/actions/setup-node/releases.
2. **llms.txt v2 link relations (optional, low urgency).** llms.txt v2 (modified 2026-08-10) recommends that each page
   point to the llms.txt that covers it: `<link rel="describedby" href="/llms.txt">`. It also suggests
   `rel="alternate" type="text/markdown"` when a Markdown version of the page exists. No page carries either link
   today. Proposed: add `<link rel="describedby" href="/llms.txt">` to the shared head (hub `index.html` source and the
   `site-page` skeleton), and skip the Markdown alternates because the site has no .md page versions. This is
   "we recommend" wording, not a requirement. Note that Google's AI-features page (2025-12-10) says no AI text files
   are needed for Google, so the benefit is limited to other agents. Source: https://llmstxt.org,
   https://llmstxt.org/changes.html.
3. **ProfilePage `dateModified` (optional).** Google's ProfilePage doc was updated 2026-09-08. The required
   `mainEntity` and `name` are both present on `/`. The recommended `dateCreated`/`dateModified` are missing. You could
   add `dateModified`, taken from the git date of the CV partials, in `scripts/gen-structured-data.py`. Source:
   https://developers.google.com/search/docs/appearance/structured-data/profile-page.
4. **External links returning 403 (blocked, not gone).** All four are bot-blocked, so no replacement is proposed:
   dl.acm.org/doi/10.1145/290941.291025, medium.com/@bayrarnorkunor/…78eb062e7fe2,
   www.lyzr.ai/glossaries/cross-validation/, www.scientific.net/EI.4.47.pdf.
5. **Long meta descriptions (validator WARN, copy).** Eight pages have descriptions between 202 and 387 characters.
   Shortening them is a wording change, so it is left to Janaka or discovery-guardian: `resume/index.html`,
   `lab/assetcare/index.html`, `academy/production-ready-spring-angular/index.html`, `academy/assetcare/index.html`,
   `blog/posts/assetcare-idea-to-production.html`, `academy/modules/2026/FSE/claude-code-configuration.html`,
   `mcp-end-to-end.html`, `mcp-primitives-lab.html`. Three of these pages are generated, so the fix belongs in their
   generators or Markdown sources.

## Watchlist
| Item | Status | Evidence | Next review |
|---|---|---|---|
| `google-search-guidance` | unchanged for us | Search gallery (updated 2026-06-15) still supports Profile page, Article, Breadcrumb and Software app. AI features page (2025-12-10): no special markup or files needed. ProfilePage doc (2026-09-08): our block has the required fields. | 2027-03-24 |
| `llms-txt-format` | v2 published, compatible | llmstxt.org v2 (modified 2026-08-10). changes.html says v1-style files remain valid. The new link relations are recommended only (proposal 2). | 2027-03-24 |
| `products-live` | reachable (reachability only) | `curl -L` returned 200 for nuechtern.app, daily-momentum.com, loop/babyloop/here.janaka.me | 2026-10-25 |
| `github-actions-versions` | newer majors exist; `checked` left null | GitHub releases API: v7 is latest for all three (proposal 1) | when Janaka applies the bump |
| `assetcare-live` | not due; https://assetcare.janaka.me/ returned 200 as a side check | curl | 2026-11-22 |
| others (`webmcp-*`, `claude-code-*`, `experience-years`, `cert-architect-exam`) | not due (checked 2026-09-25) | – | per item |

Pages naming a past year: none. Noindex or scaffold pages: 0.

## Not done and why
- Did not edit workflow files for the action bumps. Policy forbids touching `.github/workflows/`, and the item has `authority: janaka`.
- Did not shorten meta descriptions or add link relations. Both count as copy or new features (tier C).
- Did not recheck watchlist items that are not due. Did not run `weekly-brand-review` or `market-pulse`, which are out of scope.
- `docs/ai/discovery.md` has no "checked on" line to update, so I left it unchanged.
