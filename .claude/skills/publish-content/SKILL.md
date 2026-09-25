---
name: publish-content
description: Add or change public content on janaka.me and carry it through every derived surface - a new or updated project, product, blog article, Academy page, lab note, profile fact, skill or certification. Use for requests like "add my new Spring Boot project", "update AssetCare to Java 26", "publish this article", "add a certificate". Locates the canonical source, makes the factual change once, regenerates sitemap/feed/JSON-LD/llms.txt/public JSON/search, validates, and reports every surface touched.
argument-hint: "<what changed, e.g. 'new project: …' or 'AssetCare now on Java 26'>"
---

# Publish content

Load `brand-voice` for wording. Never invent facts: if the request lacks one (dates, stack, URL, status), ask or
leave the field out and say so.

## 1. Find the canonical source (change it once)

| Change | Edit here | Also visible here |
|---|---|---|
| Project or product | `content/projects.json` (slug, name, kind, summary, url, page, status, availability, stack, source …) | card in `partials/side-projects.html` (EN + `data-i18n` + DE in `assets/js/i18n.js`); products also get `<article class="card listing" id="<slug>">` in `products/index.html`; a case study gets a page (use `site-page`) |
| Identity, location, languages, skills list, links | `content/profile.json` | hub partials (`header.html`, `contact-skills-languages.html`), `resume/index.html`, `cv/print/index.html` |
| Role, certification, education | `partials/experience.html` / `certifications.html` / `education.html` | `resume/index.html`, `cv/print/index.html` (PDF: `scripts/export-cv-pdf.py`), DE dictionary, `chatbot/config.py`; the `content-guardian` agent propagates |
| Article | `blog/posts/<slug>.html` (use `new-blog-post`) | card in `blog/index.html` |
| Academy / lab page | the page under `academy/modules/2026/` or `lab/`; generated pages via their generator (table in `CLAUDE.md`) | its hub/index page link |
| A page outside `blog/posts`, `lab/Notes`, `academy/modules/2026` | the page, **and** add it to `pages` in `content/site.json` | – |

A version bump such as "Java 25 → Java 26" is a fact: grep for it (`grep -rn "Java 25" --include=*.html --include=*.json content partials resume products lab academy blog ai`), change `content/projects.json` first, then each visible copy. Derived files follow from the build.

## 2. Write the page parts

- Meta description from the page's own content (≤ ~160 chars), canonical, Open Graph, one `<h1>`.
- Hand-written Article JSON-LD only for blog posts and case studies; author `{"@id":"https://janaka.me/#me", …}`.
- Link the new content from at least one existing page (index card, related project, hub) so it is crawlable.

## 3. Regenerate and validate

```bash
python3 scripts/build.py            # hub inline, JSON-LD, content index, sitemap, feed, llms.txt, api/public/v1
python3 scripts/validate-site.py    # must end with OK
node --test "tests/js/*.test.mjs"   # when projects/profile shape changed (WebMCP reads them)
```

Then preview (`python3 -m http.server 8000`): the page, the hub card, light and dark, phone width, DE toggle.

## 4. Report

List every surface and whether it changed: page · metadata · canonical · internal links · JSON-LD · sitemap ·
feed · llms.txt · api/public/v1 · search index · WebMCP (via the JSON) · DE dictionary · CV/PDF · chatbot prompt.
Name anything left for Janaka (a PDF re-export, a fact you could not verify).

## Done when

The fact exists in exactly one source, every visible copy agrees, `validate-site.py` is OK, `build.py --check`
reports current, and the report above is written.
