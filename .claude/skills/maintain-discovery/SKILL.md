---
name: maintain-discovery
description: Keep janaka.me findable and correctly understood by search engines and AI systems - titles, meta descriptions, canonical URLs, robots, sitemap, Atom feed, Schema.org JSON-LD, internal links, llms.txt, the public JSON under /api/public/v1, duplicate pages and crawlability. Use after adding, renaming or rewriting pages, when a validator reports discovery problems, or when asked about SEO, structured data or AI discovery.
---

# Maintain discovery

Principle: search fundamentals first. Crawlable HTML, one canonical URL per page, honest titles and descriptions,
good internal links, accurate structured data. AI search consumes the same signals. No keyword stuffing, doorway or
fake-Q&A pages, no pages written for imagined AI queries, no invented markup (ratings, reviews, FAQ).

## Map

| Surface | Source | Generator |
|---|---|---|
| page inventory, sections, aliases | `content/site.json` | read by all below (`scripts/site_lib.py`) |
| JSON-LD block per page | `content/profile.json`, `content/projects.json`, page title/description | `scripts/gen-structured-data.py` |
| `assets/content-index.json` (search, related links) | pages | `scripts/gen-content-index.py` |
| `sitemap.xml` | inventory + git dates | `scripts/gen-sitemap.py` |
| `feed.xml` (Atom) | content index | `scripts/gen-feed.py` |
| `llms.txt`, `llms-full.txt`, `api/public/v1/**` | content, index, CV partials | `scripts/gen-public-data.py` |
| `robots.txt` | hand-written (small) | – |

All run, in order, from `python3 scripts/build.py`. Details and schemas: `docs/ai/discovery.md`.

## Workflow

1. `python3 scripts/validate-site.py --only inventory,meta,jsonld,sitemap,robots,feed,links,llms,public` and read
   FAILs first, then WARNs.
2. Fix at the source: page head (title, description, canonical, OG), `content/*.json`, or the generator. For a
   duplicate page, add it to `aliases` in `content/site.json` and point its canonical/og:url at the kept page;
   repoint internal links to the kept page.
3. Structured data changes go in `gen-structured-data.py` (generated block) or, for blog posts and case studies, the
   page's own Article block. Stable ids only (`#me`, `#website`, `<page>#<slug>`). Test with a real parser: the
   validator parses every block; for Google-specific eligibility use the Rich Results Test after deploy.
4. `python3 scripts/build.py`, then validate again, then `python3 -m unittest discover -s tests/python`.
5. Titles ≤ ~60 chars, descriptions ≤ ~160, carrying role, place and the strongest stack signal where natural
   (brand-voice keywords), never stuffed.

## Safety

- Never hand-edit derived files. Never change entity `@id`s (they are identities other systems cache).
- Never bump dates without a content change. Never add `noindex` to a live page without saying so.
- A breaking change to `api/public/v1` shapes needs `v2`.

## Done when

`validate-site.py` is OK, `build.py --check` reports current, and the summary lists which pages' discovery
surfaces changed and why.
