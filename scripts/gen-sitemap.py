#!/usr/bin/env python3
"""Generate sitemap.xml for janaka.me.

Run from anywhere:  python3 scripts/gen-sitemap.py
Writes <repo root>/sitemap.xml. lastmod comes from the last git commit that
touched each file (falls back to the file's mtime for untracked files).
"""
import datetime
import os
import re
import subprocess
import sys
import urllib.parse
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://janaka.me/"

# --- What goes in -----------------------------------------------------------
# Explicit pages (repo-relative). Directories are listed with a trailing slash
# and resolve to <dir>/index.html for lastmod.
EXPLICIT = [
    "",                     # hub
    "blog/",
    "blog/posts/ai-evaluation-frameworks.html",
    "blog/posts/machine-learning-blog.html",
    "blog/posts/mcp-agent-integration.html",
    "lab/",
    "products/",
    "lab/Notes/hand-book-note1.html",
    "lab/Notes/hand-book-note2.html",
    "lab/Notes/hand-book-note3.html",
    "lab/Notes/llm-hand‑annotated-demo5.html",
    "lab/Notes/llm-study-notes-handwritten-style.html",
    "ai/",
    "cv/",
    "academy/",
]
# Directory trees crawled for every *.html (recursively).
CRAWL_DIRS = ["academy/modules/2026"]

# --- What stays out ---------------------------------------------------------
# Any path matching one of these regexes (repo-relative, forward slashes) is
# dropped, both from EXPLICIT and from crawled trees.
EXCLUDE_PATTERNS = [
    r"^academy/modules/2025/",              # the whole 2025 archive
    r"BK",                                  # *BK* backup copies (indexBK.html, partials/*BK.html, ...)
    r"^partials/",                          # fetch()-assembled fragments, never standalone pages
    r"^resume-26-3-2026\.html$",            # A4 print/PDF export template
    r"coming_soon[^/]*\.html$",             # placeholder pages
    r"^blog/posts/rag-faiss-patterns\.html$",       # blog stub
    r"^blog/posts/spring-kafka-deadletter\.html$",  # blog stub
    r"^academy/modules/2026/FSE/java/",     # duplicate of the daily pages
]
EXCLUDE_RE = [re.compile(p) for p in EXCLUDE_PATTERNS]


def excluded(rel):
    return any(r.search(rel) for r in EXCLUDE_RE)


def lastmod(rel_file):
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%cs", "--", rel_file],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout.strip()
        if out:
            return out
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    ts = os.path.getmtime(os.path.join(ROOT, rel_file))
    return datetime.date.fromtimestamp(ts).isoformat()


def url_for(rel):
    # Encode each path segment; keep "/" and the trailing slash of directories.
    return BASE + "/".join(urllib.parse.quote(seg) for seg in rel.split("/"))


def collect():
    paths = []
    for rel in EXPLICIT:
        if not excluded(rel):
            paths.append(rel)
    for d in CRAWL_DIRS:
        for dirpath, _dirs, files in os.walk(os.path.join(ROOT, d)):
            for fn in sorted(files):
                if not fn.endswith(".html"):
                    continue
                rel = os.path.relpath(os.path.join(dirpath, fn), ROOT).replace(os.sep, "/")
                if not excluded(rel):
                    paths.append(rel)
    # de-duplicate, keep order
    seen, ordered = set(), []
    for p in paths:
        if p not in seen:
            seen.add(p)
            ordered.append(p)
    return ordered


def main():
    entries = []
    for rel in collect():
        file_rel = rel + "index.html" if rel == "" or rel.endswith("/") else rel
        if not os.path.exists(os.path.join(ROOT, file_rel)):
            print(f"skip (missing): {file_rel}", file=sys.stderr)
            continue
        entries.append((url_for(rel), lastmod(file_rel)))

    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, mod in entries:
        lines.append(f"  <url><loc>{escape(loc)}</loc><lastmod>{mod}</lastmod></url>")
    lines.append("</urlset>")
    out = os.path.join(ROOT, "sitemap.xml")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"wrote {out}: {len(entries)} URLs")


if __name__ == "__main__":
    main()
