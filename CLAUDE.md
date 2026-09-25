# CLAUDE.md

@AGENTS.md

The contract above (architecture, commands, canonical sources, discovery and WebMCP rules) applies in full. This file
adds how Claude Code works here. Detailed rules load by path from `.claude/rules/`; workflows are skills in
`.claude/skills/`; specialists are agents in `.claude/agents/`.

## Invariants: never break

1. A fact lives in one place (`content/*.json`, the page, or the CV partials). Derived files are regenerated with
   `python3 scripts/build.py`, never hand-edited, and committed with the change.
2. Every public content change is evaluated for impact on: the human page, metadata, canonical URL, internal links,
   structured data, sitemap, feed, llms.txt / public JSON, search index, WebMCP. Not all change; say which do.
3. The site works without JavaScript for reading, and without WebMCP entirely. `document.modelContext` appears only
   in `assets/js/agent/webmcp.js`.
4. No invented facts. The repository and the brand-voice skill are the authority.
5. Finish with `python3 scripts/validate-site.py` green (the Stop hook runs a fast version on changed files) and,
   for code under `assets/js/agent/` or `scripts/`, the tests.

## Which skill

| Request | Skill |
|---|---|
| Add or change a project, product, article, Academy page, profile fact, certification | `publish-content` |
| Titles, descriptions, canonical, JSON-LD, sitemap, feed, llms.txt, public JSON, crawlability | `maintain-discovery` |
| Add or change a WebMCP tool or its contract | `maintain-webmcp` (check the standard first: `standards-refresh`) |
| Substantial visual or interaction work | `modernize-ui` (page skeleton: `site-page`) |
| "Does it work?" after any change | `verify` |
| Before a push or a big merge | `release-readiness` |
| Before touching WebMCP, AI-discovery practice, Claude Code config or schema strategy | `standards-refresh` |
| "Run maintenance", "is anything getting stale?" (also runs weekly in CI) | `scheduled-maintenance` (agent `autonomous-maintainer`) |
| Hub copy change (EN + DE) | `i18n-add`, then the `i18n-translator` agent |
| New blog post / fill Academy scaffolds | `new-blog-post` / `fill-academy` |
| Coaching, market scan, weekly review, social copy | `/coach`, `/market-pulse`, `/weekly-brand-review`, `/linkedin-post` |

Copy for any page, post or prompt: load `brand-voice` first.

## When to use sub-agents

Use one when the work is self-contained, benefits from a specialist's checklist, or would flood the main context
(site-wide audits, parallel reviews). Do not delegate a CSS tweak, a one-line fix or anything you can verify with
one command. Ownership, so agents never redesign the same code in parallel:

| Agent | Owns |
|---|---|
| `janaka-maintainer` | orchestration of multi-domain changes; the final diff and summary |
| `content-guardian` | facts and the content model (`content/*.json`, CV partials, CV, DE dictionary, chatbot prompt) |
| `discovery-guardian` | metadata, canonical, JSON-LD, sitemap, feed, llms.txt, public JSON, internal links |
| `webmcp-guardian` | `assets/js/agent/`, the tool contract and its tests |
| `frontend-guardian` | layout, typography, tokens, responsiveness, motion, accessibility of the UI |
| `quality-guardian` | independent read-only review: security, accessibility, performance, regressions, links |
| `autonomous-maintainer` | unattended upkeep: drift in derived files, standards, links, time-sensitive facts (`content/watchlist.json`); fixes within policy, proposes the rest, deletes nothing |
| `brand-auditor`, `i18n-translator`, `content-writer`, `academy-curator`, `product-marketer`, `social-promoter`, `market-trend-analyst`, `success-coach` | voice, German, long-form writing, Academy, products, social, market, coaching |

Typical routing: CSS tweak → no agent. New project → `publish-content` (content + discovery) then `verify`.
New WebMCP capability → `webmcp-guardian`, then `quality-guardian` for security. Redesign → `frontend-guardian`,
then `discovery-guardian` and `quality-guardian` in parallel as reviewers. The main session resolves any
cross-domain conflict.

## Hooks and CI

- `.claude/settings.json` Stop hook → `scripts/hooks/stop-check.py`: when public files changed, asks for a rebuild if
  derived files are untouched and runs `validate-site.py --changed`. It never edits and steps aside after one block.
- CI (`.github/workflows/site-checks.yml`) runs `build.py --check`, `validate-site.py` and both test suites on every
  push and PR. Agents may forget; CI does not.
- No API keys anywhere. `.github/workflows/maintenance-radar.yml` (no AI) runs the staleness scan and checks every
  Monday and keeps one `maintenance` issue up to date. The AI part, `bash scripts/run-maintenance.sh [--pr]`, runs the
  `autonomous-maintainer` agent with the local Claude Code login in a throwaway worktree of `origin/main`; the script
  blocks deletions and workflow edits, re-runs every check and commits to a `maintenance/*` branch (optionally a PR,
  draft if facts changed or a check failed). It never touches the working tree or `main`.

## Repo specifics worth knowing

- Publish with `git push origin HEAD:main` after `git pull --rebase origin main`. This checkout was made by Windows
  git: keep `core.autocrlf=true` in the repo config or WSL git shows every file as modified.
- Hub behaviours (`assets/js/main.js`): the chat iframe in `partials/chat-popup.html` uses `data-src` and loads on
  first open; `toggleWorkHistory`, `showWorkHistory`, `openChatPopup`, `closeChatPopup` stay on `window` for inline
  `onclick`.
- Theme: `localStorage["jp-theme"]` = `light` | `dark`, default from the OS; copy the pre-paint `<script>` verbatim.
- `chatbot/` is a separate Gradio app on the Hugging Face Space `janaka2-claritybot.hf.space` (embedded in the chat
  modal). Reads `OPENAI_API_KEY`, `ADMIN_PASSWORD`, `RESUME_SOURCE_URL`, `PUSHOVER_*`, `SYSTEM_PROMPT` from `.env`.
  There is no deploy or weekly-review workflow in this repo; the Space is updated separately.
- Credentials: a new certificate PDF goes in `assets/certificates/`, a card in `partials/certifications.html`, a line
  in `resume/index.html`, any new `data-i18n` key in `assets/js/i18n.js`; then `scripts/build.py` (the hub inlines
  it and `api/public/v1/profile.json` picks it up).
- AssetCare (assetcare.janaka.me; repo `Janaka2/spring-angular-production-blueprint`, local clone
  `C:\data\dev\claude code\crud\spring-angular-production-blueprint`) is the live reference application. Facts live in
  `content/projects.json` and the brand-voice skill; the observability stack is an optional profile and must never be
  described as running in production. Surfaces: `partials/featured-build.html`, `lab/assetcare/`,
  `blog/posts/assetcare-idea-to-production.html`, `academy/assetcare/`, sections of `/products/`, `/ai/`, `/lab/`,
  `/academy/`, and `assets/og/assetcare.png` (`python3 scripts/gen-og-image.py assetcare`).
- Daily Academy workflows (`.github/workflows/daily_*.yml`) are off on schedule since 2026-09-15 (they published
  empty placeholders) and run only on `workflow_dispatch`; their templates are inline Python, so update them when the
  shared page chrome changes. Scaffold pages carry `noindex` and are excluded from every derived output.

### Generated Academy pages (edit the source, rerun the script, never the HTML)

| Page | Source | Generator |
|---|---|---|
| `academy/modules/2026/FSE/mcp-end-to-end.html` | `ai/mcp-momentum-planner/` | `scripts/generators/gen-mcp-page.py` |
| `academy/modules/2026/FSE/mcp-primitives-lab.html` | `ai/mcp-primitives-lab/` | `scripts/generators/gen-mcp-lab-page.py` |
| `academy/production-ready-spring-angular/index.html` | `docs/academy/ARTICLE.md` in `~/dev/spring-angular-production-blueprint` | `scripts/generators/gen-production-page.py` |
| `academy/modules/2026/FSE/claude-code-configuration.html` | `scripts/generators/content/claude-code-configuration.md` | `scripts/generators/gen-claude-config-page.py` |

These generators rewrite the whole page, so run `python3 scripts/build.py` afterwards to restore its JSON-LD block.
The last two use `scripts/generators/md2academy.py` (dialect in its docstring: `<!-- eyebrow: … -->`,
`<!-- lede -->`, `> **Label**` callouts, ```` ```flow ```` diagrams ≤ 110 columns, `::: quiz` and `::: fold`).
New study guides: a `.md` under `scripts/generators/content/` plus a ten-line config script.

`goals/vision.md` holds the personal vision the `success-coach` agent reads. `reports/` holds dated audit reports.
