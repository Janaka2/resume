# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

janaka.me — Janaka Premathilaka's personal resume site plus five sub-sites (`blog/`, `lab/`, `ai/`, `cv/`, `academy/`). Plain HTML/CSS/JS, no framework, no build step, no package manager, no tests. Hosted on GitHub Pages straight from the repo root.

## Commands

```bash
# Local preview — required, because pages assemble themselves with fetch()
# and fetch() does not work from file://
python3 -m http.server 8000     # then open http://localhost:8000/
```

There is no lint, build, or test step. Verify changes by loading the page in a browser (check both light and dark theme, and EN/DE on the hub page).

The `chatbot/` directory is a Gradio Python app deployed separately (the site embeds it via an iframe to `https://janaka2.github.io/pa/`). It reads `OPENAI_API_KEY`, `ADMIN_PASSWORD`, `RESUME_SOURCE_URL`, `PUSHOVER_*` and `SYSTEM_PROMPT` from `.env`; there is no requirements file in this repo.

## Architecture

### Partial-assembly pattern

Every page is a shell that fills `<div data-include="...">` slots at runtime via `assets/js/includes.js`. The loader fetches each partial, injects it, then fires a single `partials:loaded` event on `window`. **All behaviour scripts boot on that event**, not on `DOMContentLoaded` — anything that touches injected DOM (nav active state, theme button, tabs, i18n) must wait for it.

Two different chromes use this mechanism:

| Page | Nav | Behaviour script | Includes |
|---|---|---|---|
| Hub `/index.html` | inline `.topbar` in `index.html` | `assets/js/main.js` + `assets/js/i18n.js` | `partials/header.html`, `experience.html`, … (relative paths) |
| Sub-sites (`blog/`, `lab/`, `ai/`, `cv/`, `academy/`) | `/partials/site-nav.html` | `assets/js/site-nav.js` | root-absolute `/partials/...` paths |

`site-nav.js` derives the active nav item from the first URL path segment (`data-nav` attribute), so never hard-code an active link in `site-nav.html`.

### Design system

- `assets/css/theme.css` is the shared design system for **all** pages. Tokens live at its top (`--bg`, `--bg2`, `--tx`, `--tx2`, `--ln`, `--ac`, `--ok`, `--chip`, `--shadow`, `--r`, `--font-head`). Use tokens, never hard-coded colors.
- `assets/css/subsite.css` is layered **after** `theme.css` on sub-site pages only (never on the hub). It adds `.subhero`, `.subnav`, `.prose`, card grids, etc.
- `partials/janaka_visual_resume_v3_3.html` is the standalone one-page visual CV and the **design source of truth** — `theme.css` was extracted from it. Keep them in sync when changing visual language.
- `assets/css/styles.css` is a legacy stylesheet only referenced by some older `academy/modules/2025/FSE/*.html` pages. Don't use it for new work.
- Fonts: Archivo (headings), IBM Plex Sans (body), IBM Plex Mono — loaded from Google Fonts with the same `<link>` on every page.

### Theme and language state

- Theme: `localStorage["jp-theme"]` = `light` | `dark`, defaulting to the OS preference. Every page has the same inline pre-paint `<script>` in `<head>` that sets `data-theme` on `<html>` to avoid a flash; copy it verbatim into new pages. The toggle button is `#themeBtn`.
- Language (hub page and visual CV only): `localStorage["jp-lang"]` = `en` | `de`. English text is captured from the markup at boot; German lives in the `DE` dictionary in `assets/js/i18n.js`, keyed by `data-i18n` attributes. Adding a translatable string means adding the attribute in the partial **and** a key in the dictionary. Values may contain HTML.

### Hub page behaviours (`assets/js/main.js`)

- The chat iframe in `partials/chat-popup.html` uses `data-src`, not `src`; `main.js` copies it over on first open so the Gradio app is not loaded until requested. Keep it that way.
- `toggleWorkHistory`, `showWorkHistory`, `openChatPopup` and `closeChatPopup` are intentionally attached to `window` because partials call them from inline `onclick` attributes.

### Academy daily automation

Two GitHub Actions at `.github/workflows/` run daily and commit to `main`:

- `daily_learning_generator.yml` (05:17 UTC) — writes `academy/modules/<year>/FSE/<date>-<topic>.html` from a rotating topic pool, appends to `learning-log.md`, and inserts a link between the `<!-- DAILY_LINKS_START -->` / `<!-- DAILY_LINKS_END -->` markers in that year's `Elite‑Full‑Stack‑Engineering-*-Edition.html` (its filename contains a non-breaking hyphen U+2011; the workflow globs for it).
- `daily_update.yml` (07:00 UTC) — writes `<date>-note.html` and links it from `notes-index.html`.

Both templates are inline Python in the workflow files. If you change the shared page chrome (nav, footer, stylesheet links), update those templates too or new pages will drift. Pull before pushing — the bots commit every day.

### Archived files

`indexBK.html`, `partials/*BK.html`, `partials/janaka_visual_resume_v3.html`, `…v3_1.html`, `resumeredesign.patch`, and the root-level PDF are kept for reference only. `resume-26-3-2026.html` is a separate A4 print/PDF-export template that is intentionally not themed.
