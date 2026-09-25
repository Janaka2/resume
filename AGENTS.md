# AGENTS.md — janaka.me engineering contract

Vendor-neutral instructions for any person or coding agent working in this repository.
Claude Code reads it through `CLAUDE.md`; other tools read it directly.

## What this is

janaka.me: Janaka Premathilaka's professional site. The hub (`/`), the CV (`/resume/`; `/cv/` redirects there),
and the sub-sites `/products/`, `/lab/`, `/ai/`, `/blog/`, `/academy/`. Plain HTML, CSS and JavaScript on GitHub
Pages, served from `main` at the repo root. No framework, no bundler, no runtime dependencies. Python (stdlib) and
Node (built-in test runner) are used only for generation, validation and tests.

Guiding order: humans first, the open web second, machine readability by design, agent interaction as progressive
enhancement. Every experimental standard lives behind one adapter.

## Commands

```bash
python3 -m http.server 8000          # preview at http://localhost:8000/ (fetch() needs http, not file://)
python3 scripts/build.py             # regenerate every derived file, in order
python3 scripts/validate-site.py     # deterministic checks (see below); --changed for changed files only
node --test "tests/js/*.test.mjs"    # agent capability + WebMCP adapter tests
python3 -m unittest discover -s tests/python   # generator + validator tests
npm run check                        # all of the above, as CI runs it (npm only as a script runner)
python3 scripts/gen-og-image.py      # only after changing theme tokens (needs Pillow)
```

Verify visual changes in a browser in light and dark theme, at phone width (~375px), and in EN and DE on the hub.

## Architecture in one picture

```
content/site.json  content/profile.json  content/projects.json      the page pages (HTML) and hub partials
        \________________ canonical facts ______________/                  = canonical prose
                                   |
                         scripts/build.py (one command, deterministic, idempotent)
   build-hub.py -> gen-structured-data.py -> gen-content-index.py -> gen-sitemap.py -> gen-feed.py -> gen-public-data.py
                                   |
  HUMAN WEB                 DISCOVERY WEB                          AGENT WEB
  pages, hub inlined        sitemap.xml, robots.txt, feed.xml,    assets/js/agent/capabilities.js  (domain, DOM-free)
  (reads without JS)        JSON-LD per page, canonical URLs,      assets/js/agent/tools.js         (protocol-neutral tools)
                            llms.txt, llms-full.txt,               assets/js/agent/webmcp.js        (the only WebMCP code)
                            api/public/v1/*.json, content index
                                   |
          scripts/validate-site.py + tests/ + .github/workflows/site-checks.yml (enforcement)
```

### Canonical sources: change a fact once

| Fact | Source of truth | Derived from it (never edit these by hand) |
|---|---|---|
| Which pages exist, their section, duplicates | `content/site.json` | sitemap, content index, feed, breadcrumbs, llms.txt, API, search, WebMCP |
| Identity: name, title, location, links, languages, skills list | `content/profile.json` | Person JSON-LD (hub, CV), `api/public/v1/profile.json`, llms.txt, `get_profile` |
| Products and reference projects | `content/projects.json` | Person.owns, `/products/` ItemList, SoftwareSourceCode on case studies, `api/public/v1/projects*.json`, llms.txt, `list_projects`/`get_project` |
| Experience, certifications, education | `partials/experience.html`, `certifications.html`, `education.html` (visible CV) | parsed into `api/public/v1/profile.json`, llms-full.txt, `get_experience` |
| Page title, description, dates, text | the page itself (`<title>`, meta description, Article JSON-LD `datePublished`) | content index, feed, TechArticle JSON-LD, llms, search, `get_page` |
| Design tokens | `assets/css/theme.css` (in sync with `resume/index.html`) | OG images via `gen-og-image.py` |
| Time-sensitive facts and standards to re-check | `content/watchlist.json` | `scripts/maintenance-scan.py` report (read-only) |

Visible cards on the hub (`partials/side-projects.html`) and `/products/` stay hand-written HTML (bilingual, rich
copy). `validate-site.py` fails when they and `content/projects.json` disagree in either direction.

Generated files: `index.html` include slots (from partials), the `<script type="application/ld+json"
data-generated="gen-structured-data">` block in every page, `sitemap.xml`, `feed.xml`, `llms.txt`, `llms-full.txt`,
`assets/content-index.json`, `api/public/v1/**`. Edit the source and run `python3 scripts/build.py`. Commit derived
files with the change that caused them; CI runs `build.py --check` and fails on stale output. Merge conflicts in
derived files are never resolved by hand: take either side and rebuild.

Dates: `lastmod`/`updated` are the author date of the last non-merge commit that touched the file (today for
uncommitted changes); `date`/`datePublished` come from the page's Article JSON-LD or the first commit.

### Pages

- Every page is a shell that fills `<div data-include="...">` slots via `assets/js/includes.js`, which then fires
  `partials:loaded` on `window`; behaviour scripts boot on that event, not `DOMContentLoaded`.
- The hub is pre-assembled by `scripts/build-hub.py` (slots marked `data-inlined`, closed by `<!-- /include -->`),
  so it reads without JavaScript. Edit `partials/*.html`, never the inlined copy.
- Hub: inline `.topbar`, `assets/js/main.js` + `assets/js/i18n.js`, relative partial paths.
  Sub-sites: `/partials/site-nav.html`, `assets/js/site-nav.js` (active item from the first path segment; never
  hard-code it), root-absolute paths, `assets/css/subsite.css` after `theme.css`.
- `/resume/` is the standalone visual CV and the design source of truth for `theme.css`; it has its own top bar
  and DE dictionary. `cv/print/index.html` is the A4 PDF source (`scripts/export-cv-pdf.py`), noindex.
- Academy study pages: `class="study"` on `<body>`, `assets/css/study.css` + `assets/js/study.js` after the
  sub-site assets, one `<h1>`, real `<h2>` sections inside `.sec > .wrap`. Bump `?v=` when either file changes.
  Glossary terms: add to `assets/glossary.json`.
- Generated Academy pages (edit the source, rerun the generator): see the table in `CLAUDE.md` / `scripts/generators/`.
- New page checklist: the skeleton in `.claude/skills/site-page/SKILL.md`; the same pre-paint theme script in
  `<head>`; title, meta description (<= ~160 chars), canonical, Open Graph; one `<h1>`; `includes.js` loaded.
  A page outside the crawl roots in `content/site.json` must be added to its `pages` list or it is invisible.

### Languages

Hub and CV are English with a German toggle (`localStorage["jp-lang"]`); German lives in the `DE` dictionary in
`assets/js/i18n.js`, keyed by `data-i18n`. One URL per page, so no hreflang. Do not machine-generate translated
pages for indexing.

## Discovery rules

- Search fundamentals first: crawlable HTML, one canonical URL per page, accurate titles and descriptions,
  internal links, sitemap, feed. AI search is the same fundamentals; no "AI SEO" pages, no keyword stuffing, no
  doorway or fake Q&A pages, no mass-generated articles.
- Structured data says only what the page visibly says. Stable ids: `https://janaka.me/#me` (person),
  `https://janaka.me/#website`, `<page>#<slug>` for a product or project. Every Person reference carries `@id`.
- Near-duplicate pages go in `content/site.json` `aliases` with `rel=canonical` to the kept page.
- `llms.txt` is a convenience map for tools that read it, not a ranking signal. It is generated; keep it short.
- `api/public/v1/` is static, read-only, versioned (`apiVersion`) and public. Only already-published facts. Never
  phone numbers, credentials, tokens, the AssetCare demo password, environment data or unpublished content;
  `gen-public-data.py` refuses to write them. No OpenAPI: there is no HTTP API, only static files.

## Agent interface (WebMCP)

- Progressive enhancement: the site works identically without it. `includes.js` imports
  `assets/js/agent/webmcp.js` only when `document.modelContext` exists.
- Layers: `capabilities.js` (domain, DOM-free, injected fetch) → `tools.js` (tool descriptors, JSON-Schema input
  validation, page scoping, `{ok,data}` / `{ok:false,error:{code,message}}` results) → `webmcp.js` (the only file
  that touches `document.modelContext`; `validate-site.py` enforces this). A future remote MCP server or agent
  protocol wraps `tools.js`; it does not touch the domain.
- Tools are read-only, few (7), intent-shaped, and registered only on pages where they help. No tool may send
  messages, run code, fetch arbitrary URLs, read cookies or storage, or change content.
- Before changing WebMCP code, check the current spec (webmachinelearning.github.io/webmcp) and Chrome's docs.
  Details: `docs/ai/webmcp.md`.

## Quality bars

- Accessibility: semantic landmarks, one `<h1>`, logical headings, alt text, visible focus, keyboard reachable,
  WCAG AA contrast (tokens are checked: light `--ok` was darkened to pass), `prefers-reduced-motion` respected.
  Prefer semantic HTML over ARIA.
- Performance: no new runtime dependencies; no blocking scripts; lazy-load optional features; images sized.
- Security: treat every input (WebMCP arguments, query strings) as untrusted; no secrets in the repo
  (`chatbot/.env` is ignored); external links `rel="noopener"`; public JSON is a public interface.
- Design: tokens only (`--bg --bg2 --tx --tx2 --ln --ac --ok --chip --shadow --r --font-head`), no hard-coded
  colours, calm and technical, no gradients-and-glass trends. Fonts: Archivo, IBM Plex Sans, IBM Plex Mono.

## Facts and claims

The repository is the factual authority. Never invent employment, qualifications, certifications, clients,
metrics, testimonials, contact details or product claims. Approved wording: `.claude/skills/brand-voice/SKILL.md`.
When a fact is missing, keep the current text and flag it.

## Change impact

Before finishing, decide for each public change which surfaces it touches; `build.py` handles the derived ones.

| Change | Page | Meta/canonical | JSON-LD | Sitemap/feed | llms/API/search | WebMCP |
|---|---|---|---|---|---|---|
| Profile fact (`content/profile.json`) | hub/CV copy too | maybe | ✓ | – | ✓ | ✓ |
| Experience / certification (partials) | ✓ + DE + CV + PDF | – | – | hub lastmod | ✓ | ✓ |
| Project or product (`content/projects.json`) | hub card + /products/ or case study | – | ✓ | ✓ | ✓ | ✓ |
| New or edited article / study page | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ (via index) |
| New directory outside crawl roots | ✓ | ✓ | ✓ | add to `content/site.json` | ✓ | ✓ |
| CSS / tokens | – | – | – | – | – | – (OG images if tokens) |
| WebMCP tool | – | – | – | – | – | ✓ + tests + docs |

## Publishing

Work on a branch or locally; `git pull --rebase origin main` before `git push origin HEAD:main` (other sessions
and bots push to `main`). GitHub Pages deploys `main`. CI (`.github/workflows/site-checks.yml`) must be green.
The daily Academy workflows are disabled on schedule; when run they rebuild derived files before committing.

## Upkeep

`python3 scripts/maintenance-scan.py [--links]` lists what is going stale: watchlist items past their review date,
pages naming a past year, action pins, external links. A keyless weekly workflow
(`.github/workflows/maintenance-radar.yml`) reports it as a GitHub issue; `scripts/run-maintenance.sh` lets an
agent act on it, using a local Claude Code login rather than an API key, under a strict policy
(`.claude/skills/scheduled-maintenance/SKILL.md`): fix mechanical drift, propose everything else, never delete,
retire or rewrite anything, never change facts, and deliver only a pull request. Keep things current by upgrading in
place; mark superseded things instead of removing them.
