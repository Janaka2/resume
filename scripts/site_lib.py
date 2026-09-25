"""Shared helpers for the janaka.me generators and validators (stdlib only).

Every derived file (sitemap.xml, assets/content-index.json, feed.xml, llms.txt,
api/public/v1/*, the generated JSON-LD blocks) starts from the same three places:

    content/site.json      the page inventory: sections, pages, crawl roots, aliases
    content/profile.json   identity facts
    content/projects.json  products and reference projects

plus the HTML pages themselves (titles, descriptions, dates, text). Nothing here
writes files; the gen-*.py scripts do.
"""
import datetime
import json
import os
import re
import subprocess
import urllib.parse
from dataclasses import dataclass
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT = os.path.join(ROOT, "content")

# A page carrying any of these is an unfilled scaffold or explicitly noindex:
# it never reaches the sitemap, the index, the feed or the agent surfaces.
SCAFFOLD_MARKERS = (
    "Add today's learning notes here",     # daily_learning_generator.yml
    "Replace with the day's work",         # daily_update.yml
    'name="robots" content="noindex"',
)
MIN_BYTES = 1024                           # anything smaller is a stub


# --- content ----------------------------------------------------------------

def load_content(name, root=None):
    with open(os.path.join(root or CONTENT, name), encoding="utf-8") as fh:
        return json.load(fh)


def read(rel, root=ROOT):
    with open(os.path.join(root, rel), encoding="utf-8", errors="ignore") as fh:
        return fh.read()


# --- URLs -------------------------------------------------------------------

def site_path(rel):
    """Repo-relative file -> canonical site path ('/ai/', '/blog/posts/x.html')."""
    if rel == "index.html":
        return "/"
    if rel.endswith("/index.html"):
        rel = rel[: -len("index.html")]
    return "/" + "/".join(urllib.parse.quote(seg) for seg in rel.split("/"))


def abs_url(rel, origin="https://janaka.me"):
    return origin + site_path(rel)


def file_for_path(path):
    """Site path ('/ai/', '/x.html#frag') -> repo-relative file, or None if outside the site."""
    path = urllib.parse.unquote(path.split("#", 1)[0].split("?", 1)[0])
    if not path.startswith("/"):
        return None
    rel = path.lstrip("/")
    if rel == "" or rel.endswith("/"):
        rel += "index.html"
    return rel


# --- git dates --------------------------------------------------------------

_DATES = None


def _git_dates():
    """One pass over history: {file: (first_added, last_modified)}.

    The date is the author date (%as) of the newest / oldest non-merge commit
    that touched the file. Author dates survive `git pull --rebase`, and merge
    commits are ignored, so a branch, its pull request and main after the merge
    all compute the same dates and `scripts/build.py --check` is stable in CI.
    Files with uncommitted changes are dated today, so a page and its derived
    files can be regenerated and committed together.
    """
    global _DATES
    if _DATES is not None:
        return _DATES
    dates = {}
    try:
        out = subprocess.run(
            ["git", "-c", "core.quotePath=false", "log", "--no-renames", "--name-only", "--format=>%as"],
            cwd=ROOT, capture_output=True, text=True, check=True, encoding="utf-8",
        ).stdout
        day = None
        for line in out.splitlines():
            if line.startswith(">"):
                day = line[1:]
            elif line and day:
                first, last = dates.get(line, (day, day))
                dates[line] = (day, last)           # walking newest -> oldest
        status = subprocess.run(
            ["git", "-c", "core.quotePath=false", "status", "--porcelain", "--untracked-files=all"],
            cwd=ROOT, capture_output=True, text=True, check=True, encoding="utf-8",
        ).stdout
        today = datetime.date.today().isoformat()
        for line in status.splitlines():
            rel = line[3:].split(" -> ")[-1].strip('"')
            first, _last = dates.get(rel, (today, today))
            dates[rel] = (first, today)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    _DATES = dates
    return dates


def modified(rel):
    d = _git_dates().get(rel)
    return d[1] if d else datetime.date.fromtimestamp(os.path.getmtime(os.path.join(ROOT, rel))).isoformat()


def added(rel):
    d = _git_dates().get(rel)
    return d[0] if d else modified(rel)


# --- page inventory ---------------------------------------------------------

@dataclass
class Page:
    rel: str          # repo-relative file
    section: str
    kind: str         # "landing" | "resource"

    @property
    def path(self):
        return site_path(self.rel)

    @property
    def url(self):
        return abs_url(self.rel)


def is_scaffold(html):
    return any(m in html for m in SCAFFOLD_MARKERS)


def pages(site=None, root=ROOT, include_skipped=False):
    """The indexable pages, in manifest order. Aliases, excluded paths, stubs,
    scaffolds and noindex pages are left out (returned with a reason when
    include_skipped=True, as (Page, reason) tuples)."""
    site = site or load_content("site.json")
    exclude = [re.compile(p) for p in site.get("exclude", [])]
    landing = [re.compile(p) for p in site.get("landingPatterns", [])]
    aliases = site.get("aliases", {})

    found = [Page(p["path"], p["section"], p["kind"]) for p in site["pages"]]
    for c in site.get("crawl", []):
        base = os.path.join(root, c["dir"])
        for dirpath, dirs, files in os.walk(base):
            dirs.sort()
            if not c.get("recursive"):
                dirs[:] = []
            for fn in sorted(files):
                if fn.endswith(".html"):
                    rel = os.path.relpath(os.path.join(dirpath, fn), root).replace(os.sep, "/")
                    kind = "landing" if any(r.search(rel) for r in landing) else "resource"
                    found.append(Page(rel, c["section"], kind))

    seen, result = set(), []
    for pg in found:
        if pg.rel in seen:
            continue
        seen.add(pg.rel)
        reason = None
        full = os.path.join(root, pg.rel)
        if any(r.search(pg.rel) for r in exclude):
            reason = "excluded"
        elif pg.rel in aliases:
            reason = "alias of " + aliases[pg.rel]
        elif not os.path.isfile(full):
            reason = "missing"
        elif os.path.getsize(full) < MIN_BYTES:
            reason = "stub"
        elif is_scaffold(read(pg.rel, root)):
            reason = "scaffold/noindex"
        if include_skipped:
            result.append((pg, reason))
        elif reason is None:
            result.append(pg)
    return result


# --- HTML parsing -----------------------------------------------------------

class PageParser(HTMLParser):
    """One pass over a document: title, metas, links, JSON-LD, headings, first paragraph, visible text."""

    SKIP_TAGS = {"script", "style", "noscript", "template", "svg"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.lang = ""
        self.metas = {}
        self.links = {}           # rel -> href (first of each)
        self.hrefs = []           # every <a href> / <link href> / src, for link checking
        self.ids = set()
        self.jsonld = []
        self.headings = []        # (level, text)
        self.text_parts = []
        self.first_p = {"prose": None, "main": None, "any": None}
        self._stack = []
        self._skip = 0
        self._in_title = False
        self._in_jsonld = False
        self._ld_buf = []
        self._p_buf = None
        self._p_scope = None
        self._h_buf = None

    def _scope(self):
        prose = any("prose" in f for _t, f in self._stack)
        main = any("main" in f for _t, f in self._stack)
        return prose, main

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.add(a["id"])
        if tag == "html":
            self.lang = a.get("lang") or ""
        for attr in ("href", "src"):
            if a.get(attr) and tag in ("a", "link", "script", "img", "source", "iframe"):
                self.hrefs.append((tag, a[attr]))
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
        if tag == "link":
            for rel in (a.get("rel") or "").lower().split():
                self.links.setdefault(rel, a.get("href") or "")
            return
        if tag == "title":
            self._in_title = True
            return
        flags = set()
        if "prose" in (a.get("class") or "").split():
            flags.add("prose")
        if tag == "main":
            flags.add("main")
        self._stack.append((tag, flags))
        if tag in ("h1", "h2", "h3") and self._h_buf is None and not self._skip:
            self._h_buf = (int(tag[1]), [])
        if tag == "p" and self._p_buf is None:
            prose, main = self._scope()
            scope = "prose" if prose else ("main" if main else "any")
            if self.first_p[scope] is None:
                self._p_buf, self._p_scope = [], scope
        if tag in ("br", "hr", "img", "input"):
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
        if tag in ("h1", "h2", "h3") and self._h_buf is not None and self._h_buf[0] == int(tag[1]):
            txt = " ".join("".join(self._h_buf[1]).split())
            if txt:
                self.headings.append((self._h_buf[0], txt))
            self._h_buf = None
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
        if self._h_buf is not None:
            self._h_buf[1].append(data)

    @property
    def text(self):
        return " ".join(" ".join(self.text_parts).split())

    def description(self):
        return (self.metas.get("description") or self.first_p["prose"]
                or self.first_p["main"] or self.first_p["any"] or "")


def parse(html):
    p = PageParser()
    p.feed(html)
    p.close()
    return p


TITLE_SUFFIX_RE = re.compile(
    r"\s*(?:—|–|-|\||·)\s*(?:Janaka Premathilaka|Janaka Academy)(?:,\s*Zug)?\s*$")


def clean_title(raw):
    return TITLE_SUFFIX_RE.sub("", " ".join(raw.split())).strip()


def truncate(text, limit=200):
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    cut = text[: limit - 1]
    if " " in cut:
        cut = cut[: cut.rfind(" ")]
    return cut.rstrip(" ,;:") + "…"


def jsonld_nodes(blocks):
    """Flatten parsed JSON-LD blocks (objects, lists, @graph) into a list of dicts.
    Raises ValueError on a block that does not parse."""
    nodes = []
    for raw in blocks:
        data = json.loads(raw)
        items = data if isinstance(data, list) else [data]
        for item in items:
            if isinstance(item, dict) and isinstance(item.get("@graph"), list):
                nodes.extend(n for n in item["@graph"] if isinstance(n, dict))
            elif isinstance(item, dict):
                nodes.append(item)
    return nodes


class Node:
    """Minimal element tree for reading structured partials (experience, certifications)."""

    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}

    def __init__(self, tag, attrs=None, parent=None):
        self.tag, self.attrs, self.parent, self.children = tag, dict(attrs or {}), parent, []

    @property
    def classes(self):
        return (self.attrs.get("class") or "").split()

    def text(self):
        parts = [c if isinstance(c, str) else c.text() for c in self.children]
        return " ".join(" ".join(parts).split())

    def elements(self):
        return [c for c in self.children if isinstance(c, Node)]

    def find_all(self, tag=None, cls=None):
        out = []
        for c in self.elements():
            if (tag is None or c.tag == tag) and (cls is None or cls in c.classes):
                out.append(c)
            out.extend(c.find_all(tag, cls))
        return out

    def find(self, tag=None, cls=None):
        found = self.find_all(tag, cls)
        return found[0] if found else None


class _TreeBuilder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = self.cur = Node("#root")

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs, self.cur)
        self.cur.children.append(node)
        if tag not in Node.VOID:
            self.cur = node

    def handle_endtag(self, tag):
        n = self.cur
        while n is not None and n.tag != tag:
            n = n.parent
        if n is not None and n.parent is not None:
            self.cur = n.parent

    def handle_data(self, data):
        self.cur.children.append(data)


def dom(html):
    b = _TreeBuilder()
    b.feed(html)
    b.close()
    return b.root


def write_if_changed(path, text):
    """Write text (LF endings) only when it differs; returns True if written."""
    try:
        with open(path, encoding="utf-8", newline="") as fh:
            if fh.read().replace("\r\n", "\n") == text:
                return False
    except OSError:
        pass
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return True
