# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`janaka.me` — a personal resume site plus five sub-sites, served straight from this repo by GitHub Pages. Plain HTML/CSS/JS: **no build step, no bundler, no package manager, no test suite.** Editing a file is deploying it (push to `main` publishes).

## Running locally

Partials are injected with `fetch()`, so `file://` silently produces an empty page. Always serve over HTTP from the repo root — sub-site pages reference `/assets/...` and `/partials/...` with absolute paths, so a server rooted anywhere else breaks them:

```bash
python3 -m http.server 8000   # then http://localhost:8000/
```

The chatbot backend is a separate deployment (Hugging Face Space) and is not part of the site build:

```bash
cd chatbot && python app.py    # needs OPENAI_API_KEY; see config.py for the full env list
```

## Architecture

### Two page families, two JS entry points

Every page is assembled at runtime from `partials/*.html` by `assets/js/includes.js`, which resolves `data-include` attributes and then fires a `partials:loaded` window event. Anything that touches injected DOM must boot off that event, not `DOMContentLoaded` alone.

| | Hub (`/index.html`) | Sub-sites (`blog/ ai/ lab/ cv/ academy/`) |
|---|---|---|
| Nav | its own `.topbar` inline in `index.html` | `data-include="/partials/site-nav.html"` |
| Behaviour JS | `assets/js/main.js` (theme, EN/DE, tabs, collapsibles, chat popup) | `assets/js/site-nav.js` (active link, theme, footer year) |
| CSS | `assets/css/theme.css` | `theme.css` **then** `subsite.css` |

`site-nav.js` derives the active link from `location.pathname`'s first segment matched against `data-nav` attributes — never hard-code an active state into `site-nav.html`.

### Design system

`assets/css/theme.css` holds the tokens (`--bg`, `--bg2`, `--tx`, `--tx2`, `--ln`, `--ac`, `--ok`, `--chip`, `--shadow`, `--r`) and light/dark themes; `assets/css/subsite.css` adds only what sub-sites need on top. Use the tokens, not literal colors. `partials/janaka_visual_resume_v3_3.html` is the standalone visual CV and the **design source of truth** the tokens were extracted from — it is intentionally self-contained with zero dependencies.

Recent history is a sustained migration of one-off pages onto this system ("Align … with the design system"). New pages get `theme.css` + `subsite.css` + the shared nav and footer, never their own stylesheet. `academy/modules/*/FSE/styles.css` and `assets/css/styles.css` are leftovers from pre-migration pages; do not extend them.

Every page needs the pre-paint theme script inlined in `<head>` (copy it from `index.html`) or dark mode flashes white on load.

### State keys

`localStorage` `jp-theme` (`light`/`dark`, defaults to OS preference) and `jp-lang` (`en`/`de`, defaults to browser language). Both are shared across the hub, the sub-sites and the visual CV, so a choice follows the visitor everywhere. Any new page that offers a toggle must use the same keys.

### i18n

`assets/js/i18n.js` is hub-only. English is captured from the markup at boot; only German lives in the `DE` dictionary, keyed by `data-i18n` attributes. To add a translatable string: put the English in the HTML with `data-i18n="key"`, then add `key` to the DE dictionary. Sub-sites are English-only.

## Daily page generators (GitHub Actions)

Two scheduled workflows write into `academy/modules/<year>/FSE/` and push to `main`:

- `daily_learning_generator.yml` (05:17 UTC) — topic-rotating page `<date>-<topic>.html`, appends to `learning-log.md`, and links it into the year's `Elite-Full‑Stack-Engineering-<year>-Edition.html` between the `<!-- DAILY_LINKS_START/END -->` markers.
- `daily_update.yml` (07:00 UTC) — free-form `<date>-note.html`, indexed in `notes-index.html`.

Both are `workflow_dispatch`-able for manual runs/testing. Known traps, each already fixed once and easy to reintroduce:

- **Workflows only run from `.github/workflows/` at the repo root.** `academy/.github/workflows/` is an empty leftover; putting anything there makes it inert.
- The year comes from the current date, never a literal. Hard-coding it filed 2026 pages under 2025.
- The Elite page's real filename contains a **non-breaking hyphen (U+2011)** in "Full‑Stack". Glob for it (`Elite-Full*Stack-Engineering-*-Edition.html`); a literal `-` will not match, which silently 404s the back-link and skips the nav update.
- Both jobs need `permissions: contents: write`; the default token is read-only and the push fails.
- The generators are idempotent by design — they skip existing pages and dedupe log/index entries by href. Keep that when editing the embedded Python heredocs.

Both workflows emit their pages on the shared design system, so a change to the page template in one of these YAML heredocs is a design change.

## Chatbot (`chatbot/`)

Gradio app: `config.py` (env, system prompt, paths) → `retriever.py` (TF-IDF over `data/qa_seed.json`, `profile_facts.json` and the resume text; built at import) → `app_logic.py` → `llm.py` (OpenAI `gpt-4o-mini`) → `app.py` (UI + browser TTS JS). The system prompt has a versioned default in `config.py` and answers strictly from retrieved CONTEXT; treat its grounding and prompt-injection rules as deliberate. The site embeds the deployed Space rather than this code.

## Archived files — do not update

`indexBK.html`, `partials/*BK.html`, `partials/janaka_visual_resume_v3.html`, `…v3_1.html`, `resumeredesign.patch`. `resume-26-3-2026.html` is a separate A4 print/PDF template and is deliberately print-styled, not themed — it does not follow the design system.

## Local git note

This Windows checkout is owned by `Administratoren`, so git rejects commands with "dubious ownership". Prefix with `git -c safe.directory="C:/data/dev/claude code/resume" …`, or run `git config --global --add safe.directory 'C:/data/dev/claude code/resume'` once.
