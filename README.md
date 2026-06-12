# janaka.me — resume website

Personal resume website of **Janaka Premathilaka** — Senior Java Engineer & Solution Architect, Zug 🇨🇭.

Plain HTML/CSS/JavaScript. No frameworks, no build step — host it anywhere (GitHub Pages works as-is).

## Structure

| Path | Purpose |
|---|---|
| `index.html` | Main landing page. Assembles the sections below via `data-include` partials. |
| `partials/*.html` | Page sections (hero, experience, certifications, education, life journey, metrics, AI-assistant CTA, chat popup, contact/footer). |
| `partials/janaka_visual_resume_v3_3.html` | Standalone one-page visual CV — the **design source of truth**. Self-contained, zero dependencies. |
| `assets/css/theme.css` | Shared design system (CSS custom properties, light/dark themes) extracted from the visual CV. |
| `assets/js/includes.js` | Tiny partial loader (`fetch` → fires `partials:loaded`). |
| `assets/js/i18n.js` | EN/DE translations (`data-i18n` keys; English is captured from the markup, German lives in the dictionary). |
| `assets/js/main.js` | Theme switch, language switch, tabs, collapsible work history, chat popup. |
| `partials/*.pdf` | Downloadable CV (EN) and Lebenslauf (DE). |
| `resume-26-3-2026.html` | Separate A4 print/PDF-export CV template (intentionally print-styled, not themed). |
| `chatbot/` | Python backend powering the AI assistant (deployed separately; the site embeds it from `janaka2.github.io/pa/`). |
| `indexBK.html`, `partials/*BK.html`, `partials/janaka_visual_resume_v3.html`, `…v3_1.html` | Archived older versions, kept for reference. |

## Conventions

- **Theme**: stored in `localStorage` under `jp-theme` (`light`/`dark`), defaults to the OS preference. Shared between the main page and the visual CV.
- **Language**: stored under `jp-lang` (`en`/`de`), defaults to the browser language (English otherwise). Shared between pages too.
- **Design tokens** live at the top of `assets/css/theme.css` (`--bg`, `--bg2`, `--tx`, `--tx2`, `--ln`, `--ac`, `--ok`, `--chip`, `--shadow`, `--r`). Use them instead of hard-coded colors.

## Local preview

The partials are loaded with `fetch()`, so open the site through a local server, not `file://`:

```bash
python3 -m http.server 8000
# then open http://localhost:8000/
```
