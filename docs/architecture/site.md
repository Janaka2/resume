# Site architecture

janaka.me is static HTML on GitHub Pages. That is a deliberate choice: every page is already server-rendered in the
only sense that matters (the HTML file *is* the response), so crawlers, AI retrievers, `curl` and people without
JavaScript all receive the content. Nothing in this document requires a server, a framework or a database.

## Layers

```
                      CANONICAL KNOWLEDGE
   content/site.json · content/profile.json · content/projects.json
   pages (HTML) · hub CV partials (experience, certifications, education)
                              │
                  scripts/build.py  (stdlib Python, deterministic, idempotent)
                              │
      ┌───────────────────────┼─────────────────────────┐
  HUMAN WEB             DISCOVERY WEB                AGENT WEB
  pages, hub inlined    canonical, meta, OG          assets/js/agent/
  theme.css tokens      JSON-LD per page             capabilities → tools → webmcp
  i18n (hub, CV)        sitemap.xml, robots.txt      (progressive enhancement)
                        feed.xml (Atom)
                        llms.txt, llms-full.txt
                        api/public/v1/*.json
                        assets/content-index.json (site search)
                              │
            ENFORCEMENT: validate-site.py · tests/ · Stop hook · CI
```

## Rendering

- Sub-site pages carry their full content in the HTML; the shared nav and footer are small partials fetched by
  `assets/js/includes.js`. Without JavaScript a visitor loses the nav chrome, not the content.
- The hub is assembled from `partials/*.html`, and `scripts/build-hub.py` inlines them into `index.html` at build
  time (`data-inlined`), so the hub also reads fully without JavaScript. The loader skips inlined slots.
- `/resume/` is self-contained. `cv/print/` is the A4 PDF source (noindex).
- No user-agent-specific rendering exists or should be added.

## URLs

Stable, existing routes are kept: `/`, `/resume/` (`/cv/` redirects), `/products/` (products at `#<slug>`),
`/lab/`, `/lab/assetcare/`, `/ai/`, `/blog/`, `/blog/posts/<slug>.html`, `/academy/…`. Canonicals use the directory
form (`/ai/`, never `/ai/index.html`). GitHub Pages cannot send HTTP redirects; moved pages keep a small stub with
`<meta http-equiv="refresh">` and a canonical to the new URL (as `/cv/` and `partials/janaka_visual_resume_v3_3.html`
do). Near-duplicates are declared in `content/site.json` `aliases` and point their canonical at the kept page.

## The build

`python3 scripts/build.py` runs, in order:

| Step | Reads | Writes |
|---|---|---|
| `build-hub.py` | `partials/*.html` | `index.html` include slots |
| `gen-structured-data.py` | `content/*.json`, each page's head | the `data-generated` JSON-LD block in each page |
| `gen-content-index.py` | pages | `assets/content-index.json` |
| `gen-sitemap.py` | inventory, git dates | `sitemap.xml` |
| `gen-feed.py` | content index | `feed.xml` |
| `gen-public-data.py` | `content/*.json`, index, CV partials | `api/public/v1/**`, `llms.txt`, `llms-full.txt` |

Shared code: `scripts/site_lib.py` (inventory, URL helpers, git dates in one `git log` pass, HTML parser, mini DOM).
`build.py --check` fails when a committed derived file is stale; CI runs it.

Dates: the author date of the last non-merge commit that touched a file (stable across rebases and PR merges);
uncommitted files count as today. A page is "published" on its Article `datePublished` or its first commit.

## Enforcement

- `scripts/validate-site.py`: 11 named checks (inventory, meta, jsonld, sitemap, robots, feed, links, llms, public,
  sync, webmcp). `--changed` limits per-page checks to the working-tree diff.
- `tests/js/agent.test.mjs` (Node test runner) and `tests/python/test_site.py` (unittest). No dependencies.
- `.claude/settings.json` Stop hook runs a fast subset during Claude Code sessions.
- `.github/workflows/site-checks.yml` runs everything on every push and pull request.
- `scripts/maintenance-scan.py` + `content/watchlist.json` find drift; `.github/workflows/maintenance-radar.yml`
  reports it weekly as an issue (no AI, no keys); `scripts/run-maintenance.sh` acts on it with a local Claude Code
  login and delivers a branch or pull request (see `docs/maintenance/claude-code.md`).

## What is deliberately absent

No framework, bundler, CMS, backend, database, vector store, search service, analytics vendor, or remote MCP server.
The site search is a ~33 kB JSON index filtered in the browser. Add infrastructure only when a measured need appears.

## Observability

There is no analytics on the site and none was added. Useful signals that need no tracking: Google Search Console
(indexing, queries, structured-data reports), GitHub Pages traffic is not exposed, and the Hugging Face Space has its
own logs for the chat. If measurement is ever wanted, prefer a privacy-respecting, cookieless counter and document it
here.
