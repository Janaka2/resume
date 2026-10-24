# Maintenance 2026-10-24

**Result:** NEEDS REVIEW: nothing is broken, but the JS tests could not run (no `node` on this machine) and several proposals wait for Janaka.

## Checks
| Check | Before | After |
|---|---|---|
| build.py --check | current | current |
| validate-site.py | 0 FAIL, 8 WARN (long meta descriptions), 78 pages | same |
| JS tests (`node --test`) | not run: `node: command not found` | not run |
| Python tests | 18 OK | 18 OK |
| External links | 92 checked, 6 return 403 (bot-blocking, not gone) | unchanged |

## Changed (tiers A and B)
- `content/watchlist.json`, `webmcp-origin-trial.checked` set to 2026-10-24. Evidence: developer.chrome.com/docs/ai/webmcp still describes an origin trial "from Chrome 149" and a flag at `chrome://flags/#enable-webmcp-testing`. WebMCP does not ship by default and I saw no extension. The page gave no end date, so the 2026-11-16 date in the watchlist is not re-confirmed. `review_by` stays 2026-11-01.
- `content/watchlist.json`, `products-live.checked` set to 2026-10-24. This verified reachability only; I did not check status or copy. nuechtern.app and daily-momentum.com loaded. loop.janaka.me, babyloop.janaka.me and here.janaka.me returned their app shell ("Opening…", client-rendered) and showed no error.

## Proposals for Janaka (tier C)
- **GitHub Actions bump** (urgency: low-medium, closes the radar issue). Release pages show actions/checkout v7.0.1, actions/setup-python v7.1.0 (22 Oct) and actions/setup-node v7.1.0 (8 Oct, v7.0.0 in July).
  - Breaking notes: checkout v7 blocks fork-PR checkouts for `pull_request_target` and `workflow_run`; setup-python v7 needs Node 24 (runner >= 2.327.1) and removes the `pip-install` input; setup-node v7 moves to ESM and no longer exports a dummy `NODE_AUTH_TOKEN`.
  - None of these affects the workflows here as far as the pins show. `pip-install` and `NODE_AUTH_TOKEN` should be checked with a grep before bumping.
  - Diff: `actions/checkout@v4` → `@v7`, `actions/setup-python@v5` → `@v7`, `actions/setup-node@v4` → `@v7`, in `site-checks.yml`, `maintenance-radar.yml`, `daily_learning_generator.yml` and `daily_update.yml`.
  - Then set `checked` on `github-actions-versions`. I left it null because the item is `authority: janaka` and a version bump is not just a reachability check.
- **Shorten 8 meta descriptions to about 160 chars** (validator WARN, wording is Janaka's call). `resume/index.html` (202), `lab/assetcare/index.html` (257), `blog/posts/assetcare-idea-to-production.html` (257), `academy/assetcare/index.html` (267), `academy/production-ready-spring-angular/index.html` (317; edit the source article), `academy/modules/2026/FSE/claude-code-configuration.html` (387; edit `scripts/generators/content/claude-code-configuration.md`), `mcp-end-to-end.html` (263) and `mcp-primitives-lab.html` (295), the last two via their generators.
- **External links returning 403** (blocked, not gone): dl.acm.org, docs.racket-lang.org, medium.com, datacamp.com, lyzr.ai, scientific.net. Check by hand and replace only if actually dead.
- **Due soon:** `webmcp-origin-trial` expires 2026-11-16. Decide whether to register a token for `WEBMCP_OT_TOKEN` or leave WebMCP flag-only.
- **Still open from the handover:** `cert-architect-exam` (answer by 2026-12-31) and `experience-years` ("22+" → "23+" before 2027-05-01).

## Watchlist
| Item | Status | Evidence | Next review |
|---|---|---|---|
| webmcp-origin-trial | unchanged, checked | Chrome docs: trial from Chrome 149, not default | 2026-11-01 |
| products-live | all five answer (reachability only) | WebFetch of each URL | 2026-11-23 |
| github-actions-versions | proposal above | releases pages | on Janaka's approval |
| assetcare-live | not due until ~2026-11-22 (checked 2026-09-23; I did not re-check it this run) | – | – |
| all other items | not due | – | – |

## Not done and why
- JS tests were not run because `node` is not installed here. No `assets/js/agent/` file was changed, so the risk is low, but CI should be the judge.
- I could not use `curl` (restricted), so the liveness checks used WebFetch, which does not give HTTP status codes.
- Workflows were not edited, per policy.
- No Agent tool was available, so I did not run the quality-guardian review. The diff is a watchlist date change only, and the validator's watchlist check passes.
