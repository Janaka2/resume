# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

janaka.me — Janaka Premathilaka's personal resume site plus the sub-sites (`blog/`, `lab/`, `ai/`, `products/`, `academy/`) and the CV at `/resume/` (`/cv/` redirects there). Plain HTML/CSS/JS, no framework, no build step, no package manager, no tests. Hosted on GitHub Pages straight from the repo root.

## Commands

```bash
# Local preview — required, because pages assemble themselves with fetch()
# and fetch() does not work from file://
python3 -m http.server 8000     # then open http://localhost:8000/
```

There is no lint, build, or test step. Verify changes by loading the page in a browser (check both light and dark theme, and EN/DE on the hub page).

```bash
# After adding, renaming or rewriting any page: regenerate the derived files, in this order, and commit them
python3 scripts/gen-sitemap.py          # sitemap.xml (crawls academy/modules/2026; other pages are listed in STATIC)
python3 scripts/gen-content-index.py    # assets/content-index.json: search, related links, reading times
python3 scripts/gen-feed.py             # feed.xml, from the content index
python3 scripts/build-hub.py            # only after editing a hub partial (partials/*.html)
python3 scripts/gen-og-image.py         # only after changing theme.css tokens (needs Pillow)
```

A page outside `academy/modules/2026/` (for example `academy/production-ready-spring-angular/`) is invisible to the
crawlers until it is added to `STATIC` in `scripts/gen-sitemap.py` and to the file list at the top of
`scripts/gen-content-index.py`.

### Publishing

Work happens on the local branch `cv-photo-alignment`, which tracks `origin/main`; publish with
`git push origin HEAD:main` (GitHub Pages deploys from `main`). Other sessions and the workflows push to `main` too,
so `git pull --rebase origin main` first. Conflicts in `sitemap.xml`, `feed.xml`, `assets/content-index.json` or the
inlined `index.html` are never merged by hand: take either side and rerun the generators above.

The `chatbot/` directory is a Gradio Python app deployed separately (the site embeds the Hugging Face Space `janaka2-claritybot.hf.space` directly in the chat modal, with a waking-up skeleton and an email fallback). It reads `OPENAI_API_KEY`, `ADMIN_PASSWORD`, `RESUME_SOURCE_URL`, `PUSHOVER_*` and `SYSTEM_PROMPT` from `.env`; `chatbot/requirements.txt` pins its dependencies and `.github/workflows/deploy_chatbot.yml` uploads the folder to the Space when it changes.

## Architecture

### Partial-assembly pattern

Every page is a shell that fills `<div data-include="...">` slots at runtime via `assets/js/includes.js`. The hub is additionally pre-assembled: `python3 scripts/build-hub.py` inlines the partials into `index.html` (marked `data-inlined`, closed with an `<!-- /include -->` sentinel) so the page paints and previews without JavaScript; the loader skips those slots. **Run the build after every change to a hub partial**, or `index.html` goes stale; partials remain the source, never edit the inlined copy. The loader fetches each partial, injects it, then fires a single `partials:loaded` event on `window`. **All behaviour scripts boot on that event**, not on `DOMContentLoaded` — anything that touches injected DOM (nav active state, theme button, tabs, i18n) must wait for it.

Two different chromes use this mechanism:

| Page | Nav | Behaviour script | Includes |
|---|---|---|---|
| Hub `/index.html` | inline `.topbar` in `index.html` | `assets/js/main.js` + `assets/js/i18n.js` | `partials/header.html`, `experience.html`, … (relative paths) |
| Sub-sites (`blog/`, `lab/`, `products/`, `ai/`, `academy/`, the `lab/Notes/` pages) | `/partials/site-nav.html` | `assets/js/site-nav.js` | root-absolute `/partials/...` paths |

`site-nav.js` derives the active nav item from the first URL path segment (`data-nav` attribute), so never hard-code an active link in `site-nav.html`.

### Design system

- `assets/css/theme.css` is the shared design system for **all** pages. Tokens live at its top (`--bg`, `--bg2`, `--tx`, `--tx2`, `--ln`, `--ac`, `--ok`, `--chip`, `--shadow`, `--r`, `--font-head`). Use tokens, never hard-coded colors.
- `assets/css/subsite.css` is layered **after** `theme.css` on sub-site pages only (never on the hub). It adds `.subhero`, `.subnav`, `.prose`, card grids, etc.
- `resume/index.html` (served at `/resume/`, the hub's "View My Latest CV" target) is the standalone one-page visual CV and the **design source of truth** — `theme.css` was extracted from it. Keep them in sync when changing visual language. It is self-contained on purpose (own top bar, own DE dictionary); `partials/janaka_visual_resume_v3_3.html`, its old address, is now only a redirect stub.
- `assets/css/study.css` + `assets/js/study.js` are the **study layer** for Academy content pages (every page under `academy/modules/` except the curriculum hub). Load them after `subsite.css` / `site-nav.js` and put `class="study"` on `<body>`. The script adds, from the markup alone: a reading-progress bar, a meta line (reading time, words, sections, code samples), a collapsed "how to study this page" note, section numbers and per-section "mark done" toggles (remembered in `localStorage["jp-study:<path>"]`), an outline card when a page has three or more `<h2>`, copy buttons on `<pre>`, scroll wrappers on tables, and a resume prompt on long pages. Keep content pages to one `<h1>`, real `<h2>` sections, and the `.sec > .wrap` structure so it can find its way around. Handbook-style clusters (`Linux/`, `promting/`, `entanglement/`) link their sibling pages with a `.modnav` in the hero.
- The old page-local stylesheets (`academy/**/styles.css`, `style.css`) and the `promting/search.js` / `copy.js` helpers were removed on 2026-09-16; every Academy page now uses the shared design system.
- Fonts: Archivo (headings), IBM Plex Sans (body), IBM Plex Mono — loaded from Google Fonts with the same `<link>` on every page.

### Theme and language state

- Theme: `localStorage["jp-theme"]` = `light` | `dark`, defaulting to the OS preference. Every page has the same inline pre-paint `<script>` in `<head>` that sets `data-theme` on `<html>` to avoid a flash; copy it verbatim into new pages. The toggle button is `#themeBtn`.
- Language (hub page and visual CV only): `localStorage["jp-lang"]` = `en` | `de`. English text is captured from the markup at boot; German lives in the `DE` dictionary in `assets/js/i18n.js`, keyed by `data-i18n` attributes. Adding a translatable string means adding the attribute in the partial **and** a key in the dictionary. Values may contain HTML.

### Hub page behaviours (`assets/js/main.js`)

- The chat iframe in `partials/chat-popup.html` uses `data-src`, not `src`; `main.js` copies it over on first open so the Gradio app is not loaded until requested. Keep it that way.
- `toggleWorkHistory`, `showWorkHistory`, `openChatPopup` and `closeChatPopup` are intentionally attached to `window` because partials call them from inline `onclick` attributes.

### Academy daily automation

Two GitHub Actions at `.github/workflows/` used to run daily and commit to `main`. **Both schedules are commented out since 2026-09-15** because they published empty placeholder pages; they still run on `workflow_dispatch`. Re-enable only once the templates write real content:

- `daily_learning_generator.yml` (05:17 UTC) — writes `academy/modules/<year>/FSE/<date>-<topic>.html` from a rotating topic pool, appends to `learning-log.md`, and inserts a link between the `<!-- DAILY_LINKS_START -->` / `<!-- DAILY_LINKS_END -->` markers in that year's `Elite‑Full‑Stack‑Engineering-*-Edition.html` (its filename contains a non-breaking hyphen U+2011; the workflow globs for it).
- `daily_update.yml` (07:00 UTC) — writes `<date>-note.html` and links it from `notes-index.html`.

Both templates are inline Python in the workflow files. If you change the shared page chrome (nav, footer, stylesheet links), update those templates too or new pages will drift. Pull before pushing — the bots commit every day.

## Brand and marketing toolkit (`.claude/`)

Project-level subagents live in `.claude/agents/` and skills in `.claude/skills/`. `products/index.html` is the sales catalogue for the finished apps; keep it in step with the hub's project cards. `.claude/skills/brand-voice/SKILL.md` is the single source of truth for positioning, approved claims and ecosystem one-liners; load it before writing or reviewing any copy. `site-page` holds the HTML skeleton every new page must follow. `goals/vision.md` is the personal vision and ninety-day targets that the `success-coach` agent reads and, on request, updates.

| Need | Use |
|---|---|
| Daily or weekly coaching session | `/coach`, `/coach weekly`, `/coach decision <topic>` |
| Pre-push check | `/release-check` |
| Weekly maintenance (health + brand + SEO + academy + market) | `/weekly-brand-review` |
| Monthly market demand scan | `/market-pulse` |
| New blog post | `/new-blog-post <topic>` |
| Fill empty academy pages | `/fill-academy [N]` |
| Hub copy change | `/i18n-add`, then the `i18n-translator` agent |
| Social copy | `/linkedin-post <url>` or the `social-promoter` agent |
| Career facts changed | `cv-sync` agent |
| Product copy (nüchtern, Daily Momentum) | `product-marketer` agent |

### Generated Academy pages (edit the source, rerun the script, never the HTML)

| Page | Source | Generator |
|---|---|---|
| `academy/modules/2026/FSE/mcp-end-to-end.html` | `ai/mcp-momentum-planner/` (Python, Java, Spring code and their verified output) | `scripts/generators/gen-mcp-page.py` |
| `academy/modules/2026/FSE/mcp-primitives-lab.html` | `ai/mcp-primitives-lab/` | `scripts/generators/gen-mcp-lab-page.py` |
| `academy/production-ready-spring-angular/index.html` | `docs/academy/ARTICLE.md` in the sibling repo `~/dev/spring-angular-production-blueprint` | `scripts/generators/gen-production-page.py` |
| `academy/modules/2026/FSE/claude-code-configuration.html` | `scripts/generators/content/claude-code-configuration.md` | `scripts/generators/gen-claude-config-page.py` |

The last two use `scripts/generators/md2academy.py`, a small Markdown-to-study-page renderer (`<!-- include: @content/x.html -->` pastes an interactive block from `scripts/generators/content/`, which is how the rollout workbench and the system assembly board get into their pages) whose dialect is documented in
its docstring: `<!-- eyebrow: … -->` before a `##` names the section eyebrow, `<!-- lede -->` marks the hero lede,
`> **Label** text` becomes a callout whose flavour comes from the label (big idea / keep this → `key`, trap / warning /
limits → `warn`, memory hook / try → `try`), ```` ```flow ```` is an ASCII diagram in a `.msgflow` box, ```` ```html ````
passes through, `::: quiz Title … Answers: …  :::` renders a self-check with hidden answers, `::: fold Title … :::` a
folded block. New study-guide pages should be written this way: a `.md` under `scripts/generators/content/` plus a
ten-line config script. Keep `.msgflow` diagrams at or under 110 columns; the study CSS lets them widen to the page.

`ai/mcp-momentum-planner/` is the worked example behind the Academy guide `academy/modules/2026/FSE/mcp-end-to-end.html`: the same MCP server (plan contract, deterministic validator, save with elicitation) in Python (`mcp` 2.2), plain Java (MCP Java SDK 2.0) and Spring Boot 4 + Spring AI 2.0. The page is generated from those files, so change the code there and regenerate rather than editing the page's code blocks; all three were built and run before publishing (Python: `pytest` + `test_client.py`; Java and Spring: compiled with Maven and driven by the same client).

`.github/workflows/weekly_brand_review.yml` runs `/weekly-brand-review` every Monday via the Claude Code GitHub Action and opens a PR; it needs the `ANTHROPIC_API_KEY` repository secret.

### Credentials

Certificate PDFs live in `assets/certificates/` under descriptive names and are public. A new one is added in three
places: a card in `partials/certifications.html` (then `scripts/build-hub.py`, since the hub inlines it), a line in the
Anthropic or certifications list in `resume/index.html`, and any new `data-i18n` label in the `DE` dictionary of
`assets/js/i18n.js`. The MCP course page carries a credential badge in its hero, set in `gen-mcp-page.py`.

### Archived files

The old backups (`indexBK.html`, `partials/*BK.html`, the v3/v3_1 visual résumés, `resumeredesign.patch`, the root-level PDF and the March 2026 A4 template) were removed on 2026-09-15; git history has them. `cv/print/index.html` is the only print template: it is the A4 source for the PDF, generated with `scripts/export-cv-pdf.py`, noindex and unlinked.
