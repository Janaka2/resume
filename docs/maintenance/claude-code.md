# Maintaining janaka.me (with or without Claude Code)

Four layers keep the site consistent:

1. **Deterministic code**: `scripts/build.py` derives everything; `scripts/validate-site.py` and the tests check it.
   Works for anyone, with any editor or agent.
2. **Claude Code**: skills (workflows), sub-agents (specialist reviews) and a Stop hook, all in `.claude/`, used
   while someone is working. They do not run in the background after a session ends.
3. **CI**: `.github/workflows/site-checks.yml` enforces the same checks on every push and pull request.
4. **Autonomous upkeep, no API keys**: a keyless weekly radar in GitHub Actions reports drift as an issue, and
   `scripts/run-maintenance.sh` runs the `autonomous-maintainer` with your own Claude Code login (see below).

## Common tasks

### Add a new project (e.g. "add my new Spring Boot project")

1. Add an entry to `content/projects.json` (slug, name, kind, summary, url, page, status, availability, stack,
   source if public). Only facts you can confirm.
2. Show it: a row or card in `partials/side-projects.html` (with `data-i18n` + German in `assets/js/i18n.js`); for a
   product, an `<article class="card listing" id="<slug>">` in `products/index.html`; for a reference application, a
   case-study page (skeleton: `.claude/skills/site-page/SKILL.md`), added to `pages` in `content/site.json` if it
   sits outside the crawl roots.
3. `python3 scripts/build.py` → hub inlined, Person.owns + project node in JSON-LD, sitemap, index, llms.txt,
   `api/public/v1/projects/<slug>.json`, and the WebMCP tools see it (they read the JSON).
4. `python3 scripts/validate-site.py` (the `sync` check fails if the card and the data disagree) and `npm test`.

With Claude Code: "Add my new Spring Boot project …" → the `publish-content` skill does these steps and reports.

### Change a fact (e.g. "AssetCare moved from Java 25 to Java 26")

Edit `content/projects.json` once, then the visible copies (`grep -rn "Java 25"` across pages and partials; the
`content-guardian` agent does this), then `python3 scripts/build.py`. JSON-LD, llms.txt, the public JSON and WebMCP
follow automatically.

### New article or Academy page

Write the page (`new-blog-post` skill for posts). Anything under `blog/posts/`, `lab/Notes/` or
`academy/modules/2026/` is picked up automatically; elsewhere add it to `content/site.json`. Link it from its index,
`python3 scripts/build.py`, validate.

### Profile change (title, location, languages, links)

`content/profile.json` plus the visible hub/CV copies, then build. Career history and certifications live in the hub
partials (`experience.html`, `certifications.html`, `education.html`); the public profile JSON is parsed from them.

### Route change

Rename the file, leave a redirect stub at the old path (`<meta http-equiv="refresh">` + canonical to the new URL,
`noindex`), update internal links, adjust `content/site.json` if the page was listed there, build, validate. Never
reuse an old URL for different content.

### WebMCP standard changes

See `docs/ai/webmcp.md` → "Upgrading". Only `assets/js/agent/webmcp.js` should change.

## Claude Code system

| Kind | Name | Role |
|---|---|---|
| Contract | `AGENTS.md` (imported by `CLAUDE.md`) | vendor-neutral engineering rules |
| Rules | `.claude/rules/content.md`, `discovery.md`, `frontend.md`, `security.md` | load when matching files are read |
| Skill | `publish-content` | any content change, end to end |
| Skill | `maintain-discovery` | metadata, JSON-LD, sitemap, feed, llms, public JSON |
| Skill | `maintain-webmcp` | agent tools and adapter |
| Skill | `modernize-ui` | substantial visual work |
| Skill | `verify` | the real check commands |
| Skill | `release-readiness` | pre-push PASS/WARNING/FAIL gate |
| Skill | `standards-refresh` | re-check evolving standards before relying on them |
| Skill (existing) | `brand-voice`, `site-page`, `i18n-add`, `new-blog-post`, `fill-academy`, `weekly-brand-review`, `market-pulse`, `coach`, `linkedin-post` | voice, page skeleton, German, publishing, reviews, coaching |
| Agent | `janaka-maintainer` | orchestrates multi-domain work |
| Agent | `content-guardian` | facts and content model (was `cv-sync`) |
| Agent | `discovery-guardian` | search and AI discovery (was `seo-optimizer`) |
| Agent | `webmcp-guardian` | agent interface |
| Agent | `frontend-guardian` | UX and design system |
| Agent | `quality-guardian` | read-only review (was `site-health-checker`) |
| Agent (existing) | `brand-auditor`, `i18n-translator`, `content-writer`, `academy-curator`, `product-marketer`, `social-promoter`, `market-trend-analyst`, `success-coach` | voice, German, writing, Academy, products, social, market, coaching |
| Agent | `autonomous-maintainer` (skill `scheduled-maintenance`, runner `scripts/run-maintenance.sh`) | unattended upkeep with your Claude login; replaces no other agent |
| Hook | Stop → `scripts/hooks/stop-check.py` | when public files changed: rebuild reminder + `validate-site.py --changed` |

The hook is fast, never edits, never uses the network, and yields after blocking once per turn. The full suite
belongs to CI.

## Autonomous maintenance (no API keys)

Two parts, neither needs an API key or a repository secret:

**1. Maintenance radar (GitHub Actions, no AI).** `.github/workflows/maintenance-radar.yml` runs every Monday
04:23 UTC (or Actions → Maintenance radar → Run workflow). It runs `scripts/maintenance-scan.py --links` (watchlist
items past their review date, pages naming a past year, pinned action versions, external links), the build freshness
check, the validator and both test suites, and keeps one open issue labelled `maintenance` current. When everything is
clear it closes the issue. It only needs the default workflow token (`issues: write`).

**2. The agent run (your machine, your Claude login).**

```bash
bash scripts/run-maintenance.sh          # commit results to a local maintenance/<date> branch
bash scripts/run-maintenance.sh --pr     # ... and push it and open a pull request with gh
```

The script unsets `ANTHROPIC_API_KEY` so `claude` always uses the account you are signed in with, creates a
throwaway git worktree from `origin/main` (your working tree is never touched), and runs
`claude -p … --agent autonomous-maintainer`. The agent follows the `scheduled-maintenance` skill:

- rechecks due watchlist items against official sources and updates their `checked` dates with evidence;
- fixes mechanical drift (stale derived files, missing meta, broken internal links);
- fixes a changed standard only when the fix fits inside its adapter, and flags it;
- turns everything else into proposals in `reports/maintenance-YYYY-MM-DD.md`: every fact about you, copy, design,
  workflow version bumps, removals.

Then the script, not the model, enforces the hard rules: a deleted or renamed file discards the run, workflow edits
are reverted, every check runs again, and the result is committed to a `maintenance/*` branch. With `--pr` the pull
request is a draft labelled `needs-review` when a check failed or a fact file changed. Nothing reaches `main` until
you merge it. Logs go to `~/.cache/janaka-maintenance/`.

The runner maintains `origin/main`, so it sees this system only after it has been pushed.

**Running it on a schedule without keys** (pick one):
- Windows Task Scheduler, weekly, action
  `wsl.exe -e bash -lc "cd '/mnt/c/data/dev/claude code/resume' && bash scripts/run-maintenance.sh --pr"`.
  It runs when the PC is on and uses your Claude login inside WSL.
- A Claude Code cloud routine (`/schedule` in Claude Code) with the prompt "run the scheduled-maintenance skill and
  open a PR". It runs on your Claude account, not an API key, and needs the repository connected to Claude Code on
  the web.
- By hand, whenever the radar issue appears.

**Nothing becomes obsolete by design:** the policy upgrades in place and marks superseded things instead of deleting
them; the public JSON, entity ids, URLs and WebMCP tool contracts stay backward compatible; the existing agents and
skills keep their jobs (the maintainer reads their checklists and routes work to them through its report).

**Tuning:** add a watchlist item for any new time-sensitive dependency (`id`, `topic`, `where`, `sources`, `checked`,
`every_days` or `review_by`, `authority: agent | janaka`, `action`); `validate-site.py --only watchlist` checks the
format. Change the model or allowed tools in `scripts/run-maintenance.sh`.

## Commands

```bash
npm run check                                   # what CI runs
python3 scripts/build.py                        # regenerate
python3 scripts/validate-site.py [--changed] [--only a,b]
node --test "tests/js/*.test.mjs"
python3 -m unittest discover -s tests/python
python3 scripts/maintenance-scan.py [--links] [--json]   # read-only staleness radar
```

`npm` is only a script runner here; there are no dependencies to install.

## Line endings

The repository stores LF; this Windows checkout uses `core.autocrlf=true`. Generators write LF and only when content
changes, so they do not create CRLF churn. If WSL git shows every file as modified, run
`git config core.autocrlf true` in the repo.
