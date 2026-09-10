#!/usr/bin/env python3
"""Generate assets/content-index.json for janaka.me.

Run from anywhere:  python3 scripts/gen-content-index.py
Re-runnable; prints the number of entries written.

The index feeds the site search overlay (assets/js/search.js), the related
links block (assets/js/related.js), the Atom feed (scripts/gen-feed.py) and
the reading-time labels on blog/index.html. It is plain stdlib Python: no
BeautifulSoup, no requirements file.

Per entry: url, title, section, description, tags, date, updated, words, minutes.
"""
import datetime
import json
import math
import os
import re
import subprocess
import urllib.parse
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "content-index.json")

# Explicit single pages: (repo-relative path, section)
EXPLICIT = [
    ("ai/index.html", "ai"),
    ("products/index.html", "products"),
]
# Directories: (repo-relative dir, section, recursive)
DIRS = [
    ("blog/posts", "blog", False),
    ("academy/modules/2026/FSE", "academy", True),
    ("lab/Notes", "lab", False),
]
MIN_BYTES = 1024                     # blog stubs are a few bytes long
SKIP_BASENAMES = {"notes-index.html"}
SKIP_PATTERNS = [
    r"^academy/modules/2026/FSE/Elite[^/]*Edition\.html$",   # the year page (U+2011 in name)
    r"^academy/modules/2026/FSE/java/",                     # duplicate of the daily pages
]
SCAFFOLD_MARKERS = [
    "Add today's learning notes here",
    "Replace with the day's work",
    'name="robots" content="noindex"',
]
TITLE_SUFFIX_RE = re.compile(r"\s*(?:—|–|-|\||·)\s*(?:Janaka Premathilaka|Janaka Academy)(?:,\s*Zug)?\s*$")
STOPWORDS = {
    "a", "an", "and", "the", "for", "of", "in", "on", "to", "with", "vs", "your", "is",
    "how", "what", "why", "by", "from", "at", "as", "or", "into", "guide", "complete",
    "comprehensive", "practical", "edition", "page", "notes", "demo", "step", "learn",
}
WORDS_PER_MINUTE = 220


class PageParser(HTMLParser):
    """One pass over the document: title, metas, JSON-LD, first paragraph, visible text."""

    SKIP_TAGS = {"script", "style", "noscript", "template", "svg"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.metas = {}
        self.jsonld = []
        self.text_parts = []
        self.first_p = {"prose": None, "main": None, "any": None}
        self._stack = []          # (tag, {"prose","main"} flags)
        self._skip = 0
        self._in_title = False
        self._in_jsonld = False
        self._p_buf = None        # collecting the current <p>
        self._p_scope = None

    # -- helpers -----------------------------------------------------------
    def _scope(self):
        prose = any("prose" in f for _t, f in self._stack)
        main = any("main" in f for _t, f in self._stack)
        return prose, main

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "script":
            if (a.get("type") or "").strip().lower() == "application/ld+json":
                self._in_jsonld = True
                self._ld_buf = []
            self._skip += 1
            return
        if tag in self.SKIP_TAGS:
            self._skip += 1
            return
        if tag == "meta":
            name = (a.get("name") or a.get("property") or "").lower()
            if name and a.get("content") is not None and name not in self.metas:
                self.metas[name] = a["content"].strip()
            return
        if tag == "title":
            self._in_title = True
            return
        flags = set()
        cls = (a.get("class") or "").split()
        if "prose" in cls:
            flags.add("prose")
        if tag == "main":
            flags.add("main")
        self._stack.append((tag, flags))
        if tag == "p" and self._p_buf is None:
            prose, main = self._scope()
            scope = "prose" if prose else ("main" if main else "any")
            if self.first_p[scope] is None:
                self._p_buf, self._p_scope = [], scope
        if tag in ("br", "hr"):
            self.text_parts.append(" ")
            self._stack.pop()

    def handle_endtag(self, tag):
        if tag == "script":
            if self._in_jsonld:
                self._in_jsonld = False
                self.jsonld.append("".join(self._ld_buf))
            self._skip = max(0, self._skip - 1)
            return
        if tag in self.SKIP_TAGS:
            self._skip = max(0, self._skip - 1)
            return
        if tag == "title":
            self._in_title = False
            return
        if tag == "p" and self._p_buf is not None:
            txt = " ".join("".join(self._p_buf).split())
            if txt:
                self.first_p[self._p_scope] = txt
            self._p_buf = None
        # pop to the matching open tag (tolerates sloppy nesting)
        for i in range(len(self._stack) - 1, -1, -1):
            if self._stack[i][0] == tag:
                del self._stack[i:]
                break
        self.text_parts.append(" ")

    def handle_data(self, data):
        if self._in_jsonld:
            self._ld_buf.append(data)
            return
        if self._skip:
            return
        if self._in_title:
            self.title += data
            return
        self.text_parts.append(data)
        if self._p_buf is not None:
            self._p_buf.append(data)


def git_date(args, rel):
    try:
        out = subprocess.run(
            ["git", "log"] + args + ["--format=%cs", "--", rel],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout.split()
        return out[-1] if out else ""
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def mtime_date(rel):
    return datetime.date.fromtimestamp(os.path.getmtime(os.path.join(ROOT, rel))).isoformat()


def iso_date(value):
    """Normalise a JSON-LD date ('2025-10-19', '2025-10-19T08:00:00+02:00') to YYYY-MM-DD."""
    m = re.match(r"(\d{4}-\d{2}-\d{2})", str(value or ""))
    return m.group(1) if m else ""


def jsonld_date(blocks, key):
    for raw in blocks:
        try:
            data = json.loads(raw)
        except ValueError:
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if isinstance(item, dict):
                if item.get(key):
                    return iso_date(item[key])
                for node in item.get("@graph", []) if isinstance(item.get("@graph"), list) else []:
                    if isinstance(node, dict) and node.get(key):
                        return iso_date(node[key])
    return ""


def clean_title(raw):
    t = " ".join(raw.split())
    t = TITLE_SUFFIX_RE.sub("", t)
    return t.strip()


def derive_tags(section, keywords, title):
    if keywords:
        tags = [k.strip() for k in keywords.split(",") if k.strip()]
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


def truncate(text, limit=200):
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    cut = text[:limit - 1]
    if " " in cut:
        cut = cut[:cut.rfind(" ")]
    return cut.rstrip(" ,;:") + "…"


def url_for(rel):
    return "/" + "/".join(urllib.parse.quote(seg) for seg in rel.split("/"))


def collect():
    skip_re = [re.compile(p) for p in SKIP_PATTERNS]
    found = []
    for rel, section in EXPLICIT:
        found.append((rel, section))
    for d, section, recursive in DIRS:
        base = os.path.join(ROOT, d)
        if not os.path.isdir(base):
            continue
        for dirpath, dirs, files in os.walk(base):
            dirs.sort()
            if not recursive:
                dirs[:] = []
            for fn in sorted(files):
                if not fn.endswith(".html") or fn in SKIP_BASENAMES:
                    continue
                rel = os.path.relpath(os.path.join(dirpath, fn), ROOT).replace(os.sep, "/")
                if any(r.search(rel) for r in skip_re):
                    continue
                found.append((rel, section))
    seen, ordered = set(), []
    for item in found:
        if item[0] not in seen:
            seen.add(item[0])
            ordered.append(item)
    return ordered


def build_entry(rel, section):
    path = os.path.join(ROOT, rel)
    if not os.path.isfile(path) or os.path.getsize(path) < MIN_BYTES:
        return None
    with open(path, encoding="utf-8", errors="ignore") as fh:
        html = fh.read()
    if any(m in html for m in SCAFFOLD_MARKERS):
        return None

    p = PageParser()
    p.feed(html)
    p.close()

    title = clean_title(p.title) or os.path.splitext(os.path.basename(rel))[0]
    description = p.metas.get("description") or p.first_p["prose"] or p.first_p["main"] or p.first_p["any"] or ""
    words = len(" ".join(p.text_parts).split())
    # -m so files that entered the repo through a merge commit still report an add date
    date = jsonld_date(p.jsonld, "datePublished") or git_date(["-m", "--diff-filter=A"], rel) or mtime_date(rel)
    updated = git_date(["-1"], rel) or mtime_date(rel)

    return {
        "url": url_for(rel),
        "title": title,
        "section": section,
        "description": truncate(description),
        "tags": derive_tags(section, p.metas.get("keywords", ""), title),
        "date": date,
        "updated": updated,
        "words": words,
        "minutes": max(1, math.ceil(words / WORDS_PER_MINUTE)),
    }


def main():
    entries = []
    for rel, section in collect():
        e = build_entry(rel, section)
        if e:
            entries.append(e)
    entries.sort(key=lambda e: (e["date"], e["url"]), reverse=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(entries, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print(f"wrote {OUT}: {len(entries)} entries")


if __name__ == "__main__":
    main()
