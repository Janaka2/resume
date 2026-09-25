#!/usr/bin/env python3
"""Generate assets/content-index.json for janaka.me.

Run from anywhere:  python3 scripts/gen-content-index.py   (or scripts/build.py)

One entry per 'resource' page in content/site.json (site_lib.pages()). The index
feeds the search overlay (assets/js/search.js), the related-links block
(assets/js/related.js), the reading-time labels on blog/index.html, and, via
scripts/gen-feed.py and scripts/gen-public-data.py, the Atom feed, llms.txt,
api/public/v1/resources.json and the WebMCP tools.

Per entry: url, title, section, description, tags, date, updated, words, minutes.
"""
import json
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import site_lib  # noqa: E402

OUT = os.path.join(site_lib.ROOT, "assets", "content-index.json")
STOPWORDS = {
    "a", "an", "and", "the", "for", "of", "in", "on", "to", "with", "vs", "your", "is",
    "how", "what", "why", "by", "from", "at", "as", "or", "into", "guide", "complete",
    "comprehensive", "practical", "edition", "page", "notes", "demo", "step", "learn",
}
WORDS_PER_MINUTE = 220


def jsonld_date(blocks, key):
    try:
        nodes = site_lib.jsonld_nodes(blocks)
    except ValueError:
        return ""
    for node in nodes:
        m = re.match(r"(\d{4}-\d{2}-\d{2})", str(node.get(key) or ""))
        if m:
            return m.group(1)
    return ""


def derive_tags(section, keywords, title):
    tags = [k.strip() for k in (keywords or "").split(",") if k.strip()]
    if tags:
        return tags
    tags = [section]
    for w in re.findall(r"[A-Za-z][A-Za-z0-9+#.]*", title):
        lw = w.lower().rstrip(".")
        if len(lw) < 3 or lw in STOPWORDS or lw in tags:
            continue
        tags.append(lw)
        if len(tags) >= 5:
            break
    return tags


def build_entry(page):
    p = site_lib.parse(site_lib.read(page.rel))
    title = site_lib.clean_title(p.title) or os.path.splitext(os.path.basename(page.rel))[0]
    words = len(p.text.split())
    return {
        "url": page.path,
        "title": title,
        "section": page.section,
        "description": site_lib.truncate(p.description()),
        "tags": derive_tags(page.section, p.metas.get("keywords", ""), title),
        "date": jsonld_date(p.jsonld, "datePublished") or site_lib.added(page.rel),
        "updated": site_lib.modified(page.rel),
        "words": words,
        "minutes": max(1, math.ceil(words / WORDS_PER_MINUTE)),
    }


def build():
    entries = [build_entry(pg) for pg in site_lib.pages() if pg.kind == "resource"]
    entries.sort(key=lambda e: (e["date"], e["url"]), reverse=True)
    return entries


def main():
    entries = build()
    site_lib.write_if_changed(OUT, json.dumps(entries, ensure_ascii=False, indent=1) + "\n")
    print(f"assets/content-index.json: {len(entries)} entries")


if __name__ == "__main__":
    main()
