#!/usr/bin/env python3
"""Deterministic checks for janaka.me. Stdlib only; no network.

    python3 scripts/validate-site.py                  every check
    python3 scripts/validate-site.py --only links,meta
    python3 scripts/validate-site.py --changed        per-page checks only on files changed
                                                      in the working tree (fast; used by the hook)

Checks (FAIL blocks CI, WARN is reported):
    inventory   content/site.json pages exist; aliases point their canonical at a live target
    meta        lang, title, description, canonical = own URL, one <h1>, viewport, theme pre-paint
    jsonld      every block parses; one generated block per page; the person is always #me
    sitemap     well-formed; exactly the indexable pages; one origin; no duplicates
    robots      points at the sitemap; blocks no indexable page
    feed        well-formed Atom with entries
    links       every internal href/src in pages and partials resolves to a file
    llms        llms.txt / llms-full.txt exist and every janaka.me link resolves
    public      api/public/v1 JSON parses, is versioned, carries nothing private, links resolve
    sync        content/*.json agrees with the visible pages (projects, products, identity)
    webmcp      adapter files present, every page loads includes.js (the loader), API used only in the adapter
    watchlist   content/watchlist.json is well-formed (ids, dates, review rule, authority, action)
Freshness of generated files is `python3 scripts/build.py --check`; the WebMCP
behaviour is `node --test tests/js`; both run in CI next to this script.
"""
import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
import urllib.parse
from xml.dom import minidom

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import site_lib  # noqa: E402

ROOT = site_lib.ROOT
ORIGIN = "https://janaka.me"
SKIP_SCHEMES = ("http://", "https://", "mailto:", "tel:", "javascript:", "data:", "#", "//", "sms:", "whatsapp:")


class Report:
    def __init__(self):
        self.results = {}

    def check(self, name):
        self.results.setdefault(name, {"fail": [], "warn": []})
        return self.results[name]


def _load_module(name, file):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, file))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def resolve(page_rel, ref):
    """Internal reference from page_rel -> repo-relative file (or None to skip)."""
    ref = ref.strip()
    if not ref or ref.startswith(SKIP_SCHEMES) or "{" in ref or "${" in ref:
        return None
    path = ref.split("#", 1)[0].split("?", 1)[0]
    if not path:
        return None
    path = urllib.parse.unquote(path)
    if path.startswith("/"):
        rel = path.lstrip("/")
    else:
        rel = os.path.normpath(os.path.join(os.path.dirname(page_rel), path)).replace(os.sep, "/")
    if rel.startswith(".."):
        return rel
    if rel == "." or rel == "" or path.endswith("/"):
        rel = (rel.rstrip("/") + "/index.html").lstrip("./") if rel not in (".", "") else "index.html"
    return rel


def exists(rel):
    full = os.path.join(ROOT, rel)
    return os.path.isfile(full) or os.path.isfile(os.path.join(full, "index.html"))


def changed_files():
    out = subprocess.run(["git", "-c", "core.quotePath=false", "status", "--porcelain", "--untracked-files=all"],
                         cwd=ROOT, capture_output=True, text=True, encoding="utf-8").stdout
    return {line[3:].split(" -> ")[-1].strip('"') for line in out.splitlines()}


# --- checks ------------------------------------------------------------------

def check_inventory(r, ctx):
    c = r.check("inventory")
    for p in ctx["site"]["pages"]:
        if not os.path.isfile(os.path.join(ROOT, p["path"])):
            c["fail"].append(f"content/site.json lists a missing page: {p['path']}")
    live = {pg.rel for pg in ctx["pages"]}
    for alias, target in ctx["site"].get("aliases", {}).items():
        if not os.path.isfile(os.path.join(ROOT, alias)):
            c["warn"].append(f"alias file no longer exists: {alias}")
            continue
        if target not in live:
            c["fail"].append(f"alias {alias} points at {target}, which is not an indexable page")
        canon = site_lib.parse(site_lib.read(alias)).links.get("canonical")
        if canon != site_lib.abs_url(target):
            c["fail"].append(f"alias {alias} has canonical {canon!r}, expected {site_lib.abs_url(target)}")


def check_meta(r, ctx):
    c = r.check("meta")
    for pg in ctx["check_pages"]:
        p = ctx["parsed"][pg.rel]
        html = ctx["html"][pg.rel]
        where = pg.rel
        if not p.lang:
            c["fail"].append(f"{where}: <html> has no lang")
        if not site_lib.clean_title(p.title):
            c["fail"].append(f"{where}: empty <title>")
        desc = p.metas.get("description", "")
        if not desc:
            c["fail"].append(f"{where}: missing or empty meta description")
        elif len(desc) > 200:
            c["warn"].append(f"{where}: description is {len(desc)} chars (search shows ~160)")
        canon = p.links.get("canonical")
        if canon != pg.url:
            c["fail"].append(f"{where}: canonical {canon!r} != {pg.url}")
        h1 = sum(1 for lvl, _t in p.headings if lvl == 1)
        if h1 != 1:
            c["warn"].append(f"{where}: {h1} <h1> elements")
        if "viewport" not in p.metas:
            c["fail"].append(f"{where}: no viewport meta")
        if "jp-theme" not in html:
            c["warn"].append(f"{where}: no pre-paint theme script")
        if not p.metas.get("og:image"):
            c["warn"].append(f"{where}: no og:image")


def check_jsonld(r, ctx):
    c = r.check("jsonld")
    me = ctx["profile"]["id"]
    for pg in ctx["check_pages"]:
        p, html = ctx["parsed"][pg.rel], ctx["html"][pg.rel]
        try:
            nodes = site_lib.jsonld_nodes(p.jsonld)
        except ValueError as e:
            c["fail"].append(f"{pg.rel}: JSON-LD does not parse ({e})")
            continue
        n = html.count('data-generated="gen-structured-data"')
        if n != 1:
            c["fail"].append(f"{pg.rel}: {n} generated JSON-LD blocks (run scripts/build.py)")

        def walk(o):
            if isinstance(o, dict):
                if o.get("@type") == "Person" and o.get("name") == ctx["profile"]["name"] and o.get("@id") != me:
                    c["fail"].append(f"{pg.rel}: Person without @id {me}")
                for v in o.values():
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)
        walk(nodes)
        for node in nodes:
            if node.get("@type") in ("Article", "TechArticle", "BlogPosting") and not node.get("headline"):
                c["fail"].append(f"{pg.rel}: {node['@type']} without headline")


def check_sitemap(r, ctx):
    c = r.check("sitemap")
    try:
        doc = minidom.parse(os.path.join(ROOT, "sitemap.xml"))
    except Exception as e:  # noqa: BLE001
        c["fail"].append(f"sitemap.xml does not parse: {e}")
        return
    locs = [n.firstChild.nodeValue for n in doc.getElementsByTagName("loc")]
    if len(locs) != len(set(locs)):
        c["fail"].append("sitemap.xml has duplicate URLs")
    expected = {pg.url for pg in ctx["pages"]}
    for loc in sorted(set(locs) - expected):
        c["fail"].append(f"sitemap lists a non-indexable URL: {loc}")
    for loc in sorted(expected - set(locs)):
        c["fail"].append(f"sitemap misses {loc} (run scripts/build.py)")
    for loc in locs:
        if not loc.startswith(ORIGIN + "/"):
            c["fail"].append(f"sitemap URL outside {ORIGIN}: {loc}")


def check_robots(r, ctx):
    c = r.check("robots")
    try:
        text = site_lib.read("robots.txt")
    except OSError:
        c["fail"].append("robots.txt missing")
        return
    if f"Sitemap: {ORIGIN}/sitemap.xml" not in text:
        c["fail"].append("robots.txt does not reference the sitemap")
    disallows = [l.split(":", 1)[1].strip() for l in text.splitlines() if l.lower().startswith("disallow:")]
    for pg in ctx["pages"]:
        for d in disallows:
            if d and urllib.parse.unquote(pg.path).startswith(d):
                c["fail"].append(f"robots.txt blocks indexable page {pg.path}")


def check_feed(r, ctx):
    c = r.check("feed")
    try:
        doc = minidom.parse(os.path.join(ROOT, "feed.xml"))
    except Exception as e:  # noqa: BLE001
        c["fail"].append(f"feed.xml does not parse: {e}")
        return
    if not doc.getElementsByTagName("entry"):
        c["fail"].append("feed.xml has no entries")


def check_links(r, ctx):
    c = r.check("links")
    targets = [(pg.rel, ctx["parsed"][pg.rel]) for pg in ctx["check_pages"]]
    for fn in sorted(os.listdir(os.path.join(ROOT, "partials"))):
        rel = "partials/" + fn
        if fn.endswith(".html") and (not ctx["changed"] or rel in ctx["changed"]):
            # hub partials resolve from the hub, sub-site partials use root-absolute paths
            targets.append(("index.html", site_lib.parse(site_lib.read(rel)), rel))
    for item in targets:
        page_rel, parsed = item[0], item[1]
        label = item[2] if len(item) > 2 else page_rel
        for _tag, ref in parsed.hrefs:
            rel = resolve(page_rel, ref)
            if rel is None:
                continue
            if rel.startswith("..") or not exists(rel):
                c["fail"].append(f"{label}: broken link {ref}")


def _check_site_links(c, name, text):
    for url in re.findall(r"\]\((https://janaka\.me[^)\s]*)\)", text):
        rel = site_lib.file_for_path(url[len(ORIGIN):])
        if rel and not exists(rel):
            c["fail"].append(f"{name}: link does not resolve: {url}")


def check_llms(r, ctx):
    c = r.check("llms")
    for name in ("llms.txt", "llms-full.txt"):
        try:
            text = site_lib.read(name)
        except OSError:
            c["fail"].append(f"{name} missing (run scripts/build.py)")
            continue
        if not text.startswith("# "):
            c["fail"].append(f"{name}: must start with an H1")
        if "\n> " not in text:
            c["fail"].append(f"{name}: missing the summary blockquote")
        _check_site_links(c, name, text)
    try:
        if len(site_lib.read("llms.txt")) > 12000:
            c["warn"].append("llms.txt is over 12 kB; keep it a concise map")
    except OSError:
        pass


def check_public(r, ctx):
    c = r.check("public")
    gen = _load_module("gen_public_data", "gen-public-data.py")
    base = os.path.join(ROOT, "api", "public", "v1")
    if not os.path.isdir(base):
        c["fail"].append("api/public/v1 missing (run scripts/build.py)")
        return
    for dirpath, _d, files in os.walk(base):
        for fn in files:
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, ROOT).replace(os.sep, "/")
            try:
                with open(full, encoding="utf-8") as fh:
                    doc = json.load(fh)
            except ValueError as e:
                c["fail"].append(f"{rel}: invalid JSON ({e})")
                continue
            if doc.get("apiVersion") != gen.API_VERSION or not doc.get("canonical"):
                c["fail"].append(f"{rel}: missing apiVersion/canonical")
            try:
                gen.assert_public(doc, rel)
            except gen.PrivateDataError as e:
                c["fail"].append(str(e))
            for url in re.findall(r'"(https://janaka\.me/[^"]*)"', json.dumps(doc, ensure_ascii=False)):
                if "{slug}" in url:
                    continue
                target = site_lib.file_for_path(url[len(ORIGIN):])
                if target and not exists(target):
                    c["fail"].append(f"{rel}: link does not resolve: {url}")
    for name in ("llms.txt", "llms-full.txt"):
        try:
            gen.assert_public(site_lib.read(name), name)
        except gen.PrivateDataError as e:
            c["fail"].append(str(e))
        except OSError:
            pass


def _norm_url(u):
    u = u.lower().replace("://www.", "://")
    return u.rstrip("/")


def check_sync(r, ctx):
    c = r.check("sync")
    hub = site_lib.read("partials/side-projects.html")
    products_page = site_lib.read("products/index.html")
    products_ids = site_lib.parse(products_page).ids
    for p in ctx["projects"]:
        page_file = site_lib.file_for_path(p["page"][len(ORIGIN):])
        if not page_file or not exists(page_file):
            c["fail"].append(f"projects.json {p['slug']}: page {p['page']} does not exist")
        host = urllib.parse.urlparse(p["url"]).netloc
        if p["name"] not in hub or host not in hub:
            c["fail"].append(f"projects.json {p['slug']}: not shown on the hub (partials/side-projects.html)")
        if p["kind"] == "product":
            if p["name"] not in products_page or host not in products_page:
                c["fail"].append(f"projects.json {p['slug']}: not listed on /products/")
            frag = p["page"].split("#", 1)[1] if "#" in p["page"] else ""
            if frag and frag not in products_ids:
                c["fail"].append(f"projects.json {p['slug']}: /products/ has no #{frag} anchor")
    known = {_norm_url(p["url"]) for p in ctx["projects"]}
    for href in re.findall(r'class="popen" href="([^"]+)"', hub):
        if _norm_url(href) not in known:
            c["fail"].append(f"hub shows a product that content/projects.json lacks: {href}")
    for href in re.findall(r'<article class="card listing" id="([^"]+)"', products_page):
        if not any(p["page"].endswith("#" + href) for p in ctx["projects"]):
            c["fail"].append(f"/products/#{href} has no entry in content/projects.json")
    prof = ctx["profile"]
    hub_html = ctx["html"].get("index.html") or site_lib.read("index.html")
    hub_links = {_norm_url(u) for u in re.findall(r'href="([^"]+)"', hub_html)}
    for u in prof["sameAs"]:
        if _norm_url(u) not in hub_links and "wordpress" not in u:
            c["warn"].append(f"profile.json sameAs {u} is not linked from the hub")
    if prof["contact"]["email"] not in hub_html:
        c["fail"].append("profile.json email is not on the hub")
    if prof["name"] not in hub_html:
        c["fail"].append("profile.json name is not on the hub")


def check_webmcp(r, ctx):
    c = r.check("webmcp")
    agent = os.path.join(ROOT, "assets", "js", "agent")
    for fn in ("capabilities.js", "tools.js", "webmcp.js"):
        if not os.path.isfile(os.path.join(agent, fn)):
            c["fail"].append(f"assets/js/agent/{fn} missing")
    if "/assets/js/agent/webmcp.js" not in site_lib.read("assets/js/includes.js"):
        c["fail"].append("assets/js/includes.js does not load the WebMCP adapter")
    for pg in ctx["check_pages"]:
        if "includes.js" not in ctx["html"][pg.rel]:
            c["fail"].append(f"{pg.rel} does not load assets/js/includes.js (the WebMCP loader)")
    # the browser API may only be touched inside the adapter
    for dirpath, _d, files in os.walk(os.path.join(ROOT, "assets", "js")):
        for fn in files:
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, ROOT).replace(os.sep, "/")
            if rel in ("assets/js/agent/webmcp.js", "assets/js/includes.js"):
                continue
            with open(full, encoding="utf-8", errors="ignore") as fh:
                if "modelContext" in fh.read():
                    c["fail"].append(f"{rel} touches modelContext; keep it in assets/js/agent/webmcp.js")


def check_watchlist(r, ctx):
    import datetime
    c = r.check("watchlist")
    try:
        items = site_lib.load_content("watchlist.json")["items"]
    except (OSError, ValueError, KeyError) as e:
        c["fail"].append(f"content/watchlist.json unreadable: {e}")
        return
    seen = set()
    for i, it in enumerate(items):
        where = f"watchlist[{i}] {it.get('id', '?')}"
        for key in ("id", "topic", "action", "authority", "sources", "where"):
            if not it.get(key):
                c["fail"].append(f"{where}: missing {key}")
        if it.get("id") in seen:
            c["fail"].append(f"{where}: duplicate id")
        seen.add(it.get("id"))
        if it.get("authority") not in ("agent", "janaka"):
            c["fail"].append(f"{where}: authority must be agent or janaka")
        if not (it.get("review_by") or it.get("every_days")):
            c["fail"].append(f"{where}: needs review_by or every_days")
        for key in ("checked", "review_by"):
            if it.get(key):
                try:
                    datetime.date.fromisoformat(it[key])
                except ValueError:
                    c["fail"].append(f"{where}: {key} is not YYYY-MM-DD")


CHECKS = {
    "inventory": check_inventory, "meta": check_meta, "jsonld": check_jsonld,
    "sitemap": check_sitemap, "robots": check_robots, "feed": check_feed,
    "links": check_links, "llms": check_llms, "public": check_public,
    "sync": check_sync, "webmcp": check_webmcp, "watchlist": check_watchlist,
}
PER_PAGE = {"meta", "jsonld", "links"}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--only", help="comma-separated checks: " + ",".join(CHECKS))
    ap.add_argument("--changed", action="store_true", help="per-page checks on changed files only")
    ap.add_argument("--quiet", action="store_true", help="print failures only")
    args = ap.parse_args(argv)

    names = args.only.split(",") if args.only else list(CHECKS)
    unknown = [n for n in names if n not in CHECKS]
    if unknown:
        ap.error("unknown check(s): " + ", ".join(unknown))

    site = site_lib.load_content("site.json")
    pages = site_lib.pages(site)
    changed = changed_files() if args.changed else set()
    check_pages = [pg for pg in pages if not args.changed or pg.rel in changed]
    html = {pg.rel: site_lib.read(pg.rel) for pg in check_pages}
    ctx = {
        "site": site, "pages": pages, "check_pages": check_pages, "changed": changed,
        "profile": site_lib.load_content("profile.json"),
        "projects": site_lib.load_content("projects.json")["projects"],
        "html": html, "parsed": {rel: site_lib.parse(h) for rel, h in html.items()},
    }

    report = Report()
    for n in names:
        CHECKS[n](report, ctx)

    failed = False
    for n in names:
        res = report.results.get(n, {"fail": [], "warn": []})
        status = "FAIL" if res["fail"] else ("WARN" if res["warn"] else "PASS")
        failed |= bool(res["fail"])
        if args.quiet and status != "FAIL":
            continue
        print(f"{status:4}  {n}" + (f"  ({len(res['fail'])} fail, {len(res['warn'])} warn)" if status != "PASS" else ""))
        for msg in res["fail"]:
            print(f"      ✗ {msg}")
        if not args.quiet:
            for msg in res["warn"][:15]:
                print(f"      · {msg}")
            if len(res["warn"]) > 15:
                print(f"      · … {len(res['warn']) - 15} more warnings")
    scope = f"{len(check_pages)} changed pages" if args.changed else f"{len(pages)} pages"
    print(("FAILED" if failed else "OK") + f" — {scope}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
