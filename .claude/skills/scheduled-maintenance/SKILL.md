---
name: scheduled-maintenance
description: Unattended maintenance run for janaka.me - keeps derived files, checks, standards, links and time-sensitive facts current without deleting or retiring anything. Runs the obsolescence radar (scripts/maintenance-scan.py + content/watchlist.json), the build, validator and tests, fixes what policy allows, proposes everything else, and writes reports/maintenance-YYYY-MM-DD.md. Run by scripts/run-maintenance.sh (local Claude login, no API key) and on demand ("run maintenance", /scheduled-maintenance).
argument-hint: "[focus: all | standards | links | freshness]"
---

# Scheduled maintenance

You may be running unattended (`claude -p` from scripts/run-maintenance.sh, no human to ask). Act only inside the policy below; everything else
goes into the report as a proposal. Nobody reads the chat output of an unattended run, so the report file is the deliverable.

## Prime directive: keep it current, retire nothing

- **Never delete** a file, page, section, tool, agent, skill, rule, script, test, API field or URL. scripts/run-maintenance.sh
  discards the run if any file is deleted or renamed.
- **Never replace a working thing with a new one.** Upgrade in place; when something is truly superseded, keep it,
  mark it (`Superseded by …` note, or a redirect stub for a page) and propose removal in the report.
- **Never change a fact** about Janaka (roles, dates, certifications, claims, product status, contact details).
  Items with `authority: "janaka"` in the watchlist are propose-only. Changed `content/profile.json`,
  `content/projects.json` or CV partials turn the pull request into a draft needing review.
- **Never break a contract:** `api/public/v1` shapes, entity `@id`s, URLs, WebMCP tool names and schemas stay
  backward compatible. Additive changes only.
- **Never hand-edit derived files**; run `python3 scripts/build.py`.
- **Never** commit, push, open PRs, touch `.github/workflows/` or secrets. The runner script does git; propose
  workflow changes as diffs in the report.

## Policy

| Tier | What | How |
|---|---|---|
| A. Fix | stale derived files; validator FAILs with a mechanical fix (missing meta/OG from the page's own text, broken internal link to a moved page, missing JSON-LD block); watchlist `checked` dates after you verified the source and nothing changed; doc "checked on" dates | edit, rebuild, re-validate |
| B. Fix and flag | a standard changed in a breaking or deprecated way and the fix fits inside its adapter (`assets/js/agent/webmcp.js` + test fake; a generator; Claude Code config syntax) with all tests green | edit, mark **Needs careful review** in the report |
| C. Propose | anything with `authority: "janaka"`; copy or wording; new pages, tools or features; design; long descriptions; external link failures; action version bumps; removal of anything | report only, with the exact diff or wording |

When unsure, choose the more conservative tier.

## Run

1. **Baseline.** `git status --short`, then:
   ```bash
   python3 scripts/maintenance-scan.py --links       # radar; add --today only in tests
   python3 scripts/build.py --check
   python3 scripts/validate-site.py
   node --test "tests/js/*.test.mjs"
   python3 -m unittest discover -s tests/python
   ```
   Record every result for the report.
2. **Repair (tier A).** Stale derived files → `python3 scripts/build.py`. Validator FAILs → fix at the source per the
   `maintain-discovery` and `verify` skills.
3. **Watchlist.** For each item the radar lists: open its `sources` (WebFetch; official documentation only), compare
   with its `where` files, then
   - unchanged → set `checked` to today in `content/watchlist.json` (tier A) and note the evidence (URL + what you saw);
   - changed and `authority: agent` → follow `standards-refresh`: tier B if the fix fits one adapter, else tier C;
   - `authority: janaka` → tier C proposal; do not touch `checked` unless you only verified reachability (e.g. a URL
     answered 200), and say so.
   Add a new watchlist item when you find a new time-sensitive dependency (adding is allowed; removing is not).
4. **Links.** Internal breakage is a validator FAIL (tier A). External failures are tier C: separate "gone"
   (404/410, DNS) from "blocked or flaky" (401/403/429/5xx, timeouts); propose replacements for the gone ones only.
5. **Freshness.** Pages naming a past year in title or `<h1>` → tier C proposal (never rename a URL). Academy
   scaffolds → mention; filling them is the `fill-academy` skill's job, not this run's.
6. **Review.** If the Agent tool is available, ask `quality-guardian` to review your diff (and `webmcp-guardian` for
   any `assets/js/agent/` change). If it is not (you are running as a sub-agent), read
   `.claude/agents/quality-guardian.md` and apply its checklist yourself.
7. **Verify.** Re-run the five commands from step 1. Everything must pass, or revert your own change that broke it
   (`git checkout -- <file>` on files you changed) and report the failure instead.
8. **Report.** Write `reports/maintenance-YYYY-MM-DD.md`:

```markdown
# Maintenance YYYY-MM-DD

**Result:** PASS | NEEDS REVIEW | FAIL — one sentence.

## Checks
| Check | Before | After |
(build --check, validator, JS tests, Python tests, links)

## Changed (tiers A and B)
- file — what and why (evidence link). Tier B items marked **Needs careful review**.

## Proposals for Janaka (tier C)
- item — exact proposed change (diff or wording), source, urgency.

## Watchlist
| Item | Status | Evidence | Next review |

## Not done and why
```

Keep it short and factual. If nothing needed doing, still write the report (it proves the run happened) and change
nothing else.

## Done when

The report exists, every change is within tiers A–B, no file was deleted, and all checks pass.
