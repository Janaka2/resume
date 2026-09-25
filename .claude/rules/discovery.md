---
paths:
  - "content/site.json"
  - "scripts/**"
  - "sitemap.xml"
  - "feed.xml"
  - "robots.txt"
  - "llms.txt"
  - "llms-full.txt"
  - "api/**"
  - "assets/content-index.json"
  - "**/*.html"
---

# Discovery rules

- Derived files are never edited by hand: `sitemap.xml`, `feed.xml`, `llms.txt`, `llms-full.txt`,
  `assets/content-index.json`, `api/public/v1/**`, and the `data-generated="gen-structured-data"` JSON-LD block in
  every page. Change the source, run `python3 scripts/build.py`, commit both. Conflicts: take either side, rebuild.
- The page inventory is `content/site.json`. A page outside `crawl` roots is invisible until added to `pages`.
- Canonical: `https://janaka.me/<path>`, directories with a trailing slash, `index.html` never in a URL.
- Structured data only states what the page shows. Stable ids: `https://janaka.me/#me`, `https://janaka.me/#website`,
  `<page>#<slug>`. No invented ratings, reviews, prices, FAQ or HowTo markup.
- Search fundamentals beat AI tricks: no keyword stuffing, doorway pages, fake Q&A, or pages written for imagined
  AI queries. llms.txt is a convenience, not a ranking lever.
- `lastmod` comes from git (author date of the last non-merge commit); never bump dates to look fresh.
- Public JSON is versioned (`apiVersion`); a breaking shape change means `v2`, not an edit of `v1`.
- Validate: `python3 scripts/validate-site.py` (all) or `--only meta,jsonld,sitemap,links,llms,public`.
- Generator code: stdlib only, deterministic, idempotent (running twice changes nothing), LF output via
  `site_lib.write_if_changed`. Add a test in `tests/python/` for new behaviour.
