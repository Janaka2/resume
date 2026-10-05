# Maintenance 2026-10-05

**Result:** NEEDS REVIEW — the site is current and the checks pass, but the JS tests could not run here and two items need Janaka.

## Checks
| Check | Before | After |
|---|---|---|
| build.py --check | current | current |
| validate-site.py | OK, 78 pages, 8 WARN (meta descriptions > 160 chars) | same |
| JS tests (`node --test`) | **not run: `node` is not installed in this environment** | not run |
| Python tests | 18 OK | not re-run (only `content/watchlist.json` changed; the validator watchlist check passes) |
| External links | 92 checked, 4 return 403 (blocked, not gone) | unchanged |

No JS file changed in this run, so the missing JS run is low risk. CI runs it.

## Changed (tiers A and B)
- `content/watchlist.json` — `products-live.checked` set to 2026-10-05. Reachability only: nuechtern.app, daily-momentum.com, loop.janaka.me, babyloop.janaka.me and here.janaka.me all loaded through WebFetch. loop, babyloop and here showed an "Opening…" shell, which is the app's client-side start-up, not an error. This is a reachability check only, and the product copy and status are untouched.

## Proposals for Janaka (tier C)
- **GitHub Actions majors** (urgency: low, not urgent). The release pages show v7 as the latest major for `actions/checkout` (v7.0.1), `actions/setup-python` (v7.0.0) and `actions/setup-node` (v7.0.0). The workflows pin v4, v5 and v4.
  - Notes from the releases:
    - checkout v7 blocks fork-PR checkout under `pull_request_target` and `workflow_run`. None of this repo's workflows appear to use those triggers.
    - setup-python v7 moves to ESM and removes the `pip-install` input.
    - setup-python needs runner ≥ 2.327.1 (the Node 24 move came in v6). GitHub-hosted runners meet that.
    - setup-node v7 moves to ESM and no longer exports a dummy `NODE_AUTH_TOKEN`.
  - Release dates in the fetched summaries looked wrong, so confirm on the pages before bumping.
  - Proposed diff in `site-checks.yml`, `maintenance-radar.yml`, `daily_learning_generator.yml` and `daily_update.yml`: `actions/checkout@v4` → `@v7`, `actions/setup-python@v5` → `@v7`, `actions/setup-node@v4` → `@v7`. Then set `github-actions-versions.checked`. I left `checked` as null because nothing has been bumped. That item stays open, as does issue #18.
- **Meta descriptions over 160 chars** (8 pages, unchanged from the handover list). `production-ready-spring-angular` is now 317 chars, not 335. Wording is Janaka's call. Generated pages need their source or generator changed (see CLAUDE.md).
- **Four external links return 403**: dl.acm.org, medium.com, lyzr.ai and scientific.net. This is bot-blocking, not "gone". Check them by hand and replace one only if it is dead.
- Other open items on the CLAUDE.md handover list (Search Console, origin trial token, `modenizeJava.html` API key, `cert-architect-exam` by 2026-12-31, "22+" → "23+" before 2027-05-01) are unchanged.

## Watchlist
| Item | Status | Evidence | Next review |
|---|---|---|---|
| github-actions-versions | never checked, proposal above | release pages, v7 on all three | after Janaka bumps |
| products-live | reachable, `checked` updated | 5 URLs loaded | 2026-11-04 |
| assetcare-live | not due (checked 2026-09-23, every 60 days) | – | 2026-11-22 |
| webmcp-origin-trial | review_by 2026-11-01 (not yet due) | – | 2026-11-01 |
| other items | not due | – | per the watchlist |

## Not done and why
- JS tests: `node` is missing in this environment.
- Reachability checks used WebFetch because `curl` was not permitted. They confirm the pages load, not exact HTTP status codes.
- No standards refresh: no standards item was due.
- Past-year pages: none. Scaffold pages: 0.
- Nothing was deleted, no workflow was edited, and nothing was committed.
