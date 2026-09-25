---
name: verify
description: Verify a change to janaka.me with the repository's real commands - rebuild derived files, run the deterministic site validator, the WebMCP/agent tests and the generator tests, and preview in a browser. Use after any code or content change, when asked "does it work?", or before handing work back.
allowed-tools:
  - Bash(python3 scripts/build.py:*)
  - Bash(python3 scripts/validate-site.py:*)
  - Bash(node --test:*)
  - Bash(python3 -m unittest:*)
  - Bash(git status:*)
  - Bash(git diff:*)
  - Bash(python3 scripts/maintenance-scan.py:*)
---

# Verify

The site has no compile, lint or typecheck step (plain HTML/CSS/JS). These are the real checks, fastest first:

```bash
git status --short                                   # what changed
python3 scripts/build.py                             # regenerate; a second run must change nothing
python3 scripts/validate-site.py                     # inventory meta jsonld sitemap robots feed links llms public sync webmcp
node --test "tests/js/*.test.mjs"                    # agent capabilities + WebMCP adapter (19+ tests)
python3 -m unittest discover -s tests/python         # generators, inventory, propagation, private-data guard
```

`npm run check` runs the same set as CI (`build.py --check` + validator + both suites).
`python3 scripts/maintenance-scan.py [--links]` is the read-only staleness radar (watchlist, past years, pins, links).

Quick variants: `python3 scripts/validate-site.py --changed` (per-page checks on changed files only),
`--only links,meta`.

Browser (anything visual or behavioural): `python3 -m http.server 8000`, open the changed pages, check light and
dark, ~375px width, EN/DE on the hub, and the console for errors. A page must read fully with JavaScript disabled.

Report as PASS / WARN / FAIL per line (build, validator, JS tests, Python tests, browser) with the failing output
quoted. Fix root causes; never weaken a check or a test to get green.

Keep this skill current: when a command, check or test suite is added, update the list above.
