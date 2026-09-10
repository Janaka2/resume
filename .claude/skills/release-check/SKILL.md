---
name: release-check
description: Pre-push gate for janaka.me - runs the site-health-checker on the working tree, confirms i18n parity, regenerates sitemap.xml, and blocks on any P1 finding. Use before every push to main.
---

# Release check

1. `git status --short` — list what is about to ship.
2. Launch `site-health-checker`. If it reports any broken internal link, missing include, or missing chrome on a changed page, stop and fix before continuing.
3. If any hub partial or `i18n.js` changed, run the verification block from the `i18n-add` skill; zero missing DE keys required.
4. If any hub partial changed, run `python3 scripts/build-hub.py` and stage `index.html`. If any HTML page was added, renamed or written, run `python3 scripts/gen-sitemap.py`, `python3 scripts/gen-content-index.py` and `python3 scripts/gen-feed.py` and stage `sitemap.xml`, `assets/content-index.json` and `feed.xml`.
5. `git pull --rebase` (the academy bots commit daily), then push.
6. Report in three lines: files shipped, checks passed, anything deferred.
