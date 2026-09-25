---
name: release-readiness
description: Pre-push gate for janaka.me - build freshness, validator, tests, links, metadata, canonical URLs, sitemap, structured data, llms.txt and public JSON, WebMCP, i18n parity, plus accessibility, security and performance sanity on the changed pages. Produces a PASS/WARNING/FAIL table and blocks on any FAIL. Use before every push to main or a substantial merge.
---

# Release readiness

1. `git status --short` and `git diff --stat`: what is about to ship.
2. Deterministic gate (all must pass):
   ```bash
   python3 scripts/build.py --check      # derived files current (run build.py and stage if not)
   python3 scripts/validate-site.py
   node --test "tests/js/*.test.mjs"
   python3 -m unittest discover -s tests/python
   ```
3. If a hub partial or `assets/js/i18n.js` changed: the verification block of the `i18n-add` skill; zero missing DE
   keys.
4. Judgement review of the changed files only. Launch `quality-guardian` on the diff (security, accessibility,
   performance, regressions, private data). For a large content or structure change, launch `discovery-guardian` in
   parallel.
5. `git pull --rebase origin main` (other sessions and bots push to `main`); if derived files conflict, take either
   side and rerun `python3 scripts/build.py`. Push with `git push origin HEAD:main` only when asked.
6. Report:

| Area | Result | Note |
|---|---|---|
| Build freshness | PASS/WARNING/FAIL | |
| Tests (JS, Python) | | |
| Links, metadata, canonical | | |
| Sitemap, feed, robots | | |
| Structured data | | |
| llms.txt, public JSON | | |
| WebMCP | | |
| i18n | | |
| Accessibility sanity | | |
| Security sanity | | |
| Performance sanity | | |

Any FAIL blocks the push. WARNINGs are listed with a recommendation.
