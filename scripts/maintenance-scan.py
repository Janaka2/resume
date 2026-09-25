#!/usr/bin/env python3
"""Obsolescence radar for janaka.me. Read-only; never edits a file.

    python3 scripts/maintenance-scan.py              markdown report on stdout
    python3 scripts/maintenance-scan.py --links      also check external links (network)
    python3 scripts/maintenance-scan.py --json       machine-readable
    python3 scripts/maintenance-scan.py --today 2027-05-02   pretend another date (tests)

What it looks for, so the autonomous maintenance run (and anyone else) starts
from facts instead of guesses:

    watchlist   content/watchlist.json items past or near their review date
    stale-year  indexable pages whose title or <h1> names a past year
    pins        GitHub Actions `uses:` pins, for comparison with upstream releases
    scaffolds   unfilled Academy scaffolds and other noindex pages
    links       (--links) external URLs that do not answer 2xx/3xx

The derived-file freshness, validator and tests are separate commands
(scripts/build.py --check, scripts/validate-site.py, the test suites); the
scheduled-maintenance skill runs all of them.
"""
import argparse
import concurrent.futures
import datetime
import json
import os
import re
import sys
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import site_lib  # noqa: E402

ROOT = site_lib.ROOT
DUE_SOON_DAYS = 21
USER_AGENT = "janaka.me-maintenance-scan/1 (+https://janaka.me/)"


def _date(s):
    return datetime.date.fromisoformat(s) if s else None


def watchlist(today, items=None):
    """Return [{id, status, due, …}] for items overdue, due soon, or never checked."""
    if items is None:
        items = site_lib.load_content("watchlist.json")["items"]
    out = []
    for it in items:
        checked = _date(it.get("checked"))
        if it.get("review_by"):
            due = _date(it["review_by"])
        elif it.get("every_days"):
            due = checked + datetime.timedelta(days=int(it["every_days"])) if checked else None
        else:
            due = None
        if checked is None and not it.get("review_by"):
            status = "never-checked"
        elif due and due < today:
            status = "overdue"
        elif due and (due - today).days <= DUE_SOON_DAYS:
            status = "due-soon"
        else:
            continue
        out.append({"id": it["id"], "status": status, "due": due.isoformat() if due else None,
                    "authority": it.get("authority", "janaka"), "topic": it["topic"],
                    "action": it["action"], "sources": it.get("sources", []), "where": it.get("where", [])})
    order = {"overdue": 0, "never-checked": 1, "due-soon": 2}
    return sorted(out, key=lambda r: (order[r["status"]], r["due"] or ""))


def stale_years(today, pages=None):
    """Indexable pages whose <title> or <h1> mentions a year before the current one."""
    out = []
    for pg in pages if pages is not None else site_lib.pages():
        p = site_lib.parse(site_lib.read(pg.rel))
        texts = [site_lib.clean_title(p.title)] + [t for lvl, t in p.headings if lvl == 1]
        years = {int(y) for t in texts for y in re.findall(r"\b(20\d\d)\b", t)}
        past = sorted(y for y in years if y < today.year)
        # a page that also names the current year (e.g. "Java 8 to 27, 2004-2026") is not stale
        if past and today.year not in years:
            out.append({"page": pg.path, "years": past, "title": texts[0]})
    return out


def action_pins():
    pins = []
    wf = os.path.join(ROOT, ".github", "workflows")
    for fn in sorted(os.listdir(wf)):
        if fn.endswith((".yml", ".yaml")):
            with open(os.path.join(wf, fn), encoding="utf-8") as fh:
                for m in re.finditer(r"uses:\s*([\w.-]+/[\w.-]+)@([\w.-]+)", fh.read()):
                    pins.append({"workflow": fn, "action": m.group(1), "ref": m.group(2)})
    return pins


def noindex_pages():
    found = []
    for pg, reason in site_lib.pages(include_skipped=True):
        if reason == "scaffold/noindex":
            found.append(pg.path)
    return found


def external_urls():
    urls = set()
    for pg in site_lib.pages():
        for _tag, ref in site_lib.parse(site_lib.read(pg.rel)).hrefs:
            if ref.startswith(("http://", "https://")) and "janaka.me" not in ref.split("/")[2]:
                urls.add(ref.split("#", 1)[0])
    for name in ("profile.json", "projects.json"):
        text = json.dumps(site_lib.load_content(name))
        urls.update(u for u in re.findall(r'"(https?://[^"]+)"', text) if "janaka.me/" not in u)
    skip = ("fonts.googleapis.com", "fonts.gstatic.com", "wa.me", "linkedin.com", "schema.org")
    return sorted(u for u in urls if not any(s in u for s in skip))


def check_url(url):
    for method in ("HEAD", "GET"):
        req = urllib.request.Request(url, method=method, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return url, r.status
        except urllib.error.HTTPError as e:
            if method == "HEAD" and e.code in (403, 405, 429, 501):
                continue
            return url, e.code
        except Exception as e:  # noqa: BLE001  network errors are findings, not crashes
            if method == "GET":
                return url, type(e).__name__
    return url, "unknown"


def link_report():
    urls = external_urls()
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(check_url, urls))
    return {"checked": len(urls),
            "failing": [{"url": u, "status": s} for u, s in results if not (isinstance(s, int) and s < 400)]}


def render_markdown(report):
    L = [f"# Maintenance scan {report['today']}", ""]
    L += ["## Watchlist", ""]
    if report["watchlist"]:
        L += ["| Item | Status | Due | Authority | Action |", "|---|---|---|---|---|"]
        for w in report["watchlist"]:
            L.append(f"| `{w['id']}` | {w['status']} | {w['due'] or '–'} | {w['authority']} | {w['action']} |")
    else:
        L.append("Nothing due.")
    L += ["", "## Pages naming a past year", ""]
    L += [f"- {s['page']}: {s['title']} ({', '.join(map(str, s['years']))})" for s in report["stale_years"]] or ["None."]
    L += ["", "## GitHub Actions pins", ""]
    L += [f"- {p['workflow']}: `{p['action']}@{p['ref']}`" for p in report["pins"]]
    L += ["", f"## Noindex / scaffold pages: {len(report['noindex'])}", ""]
    L += [f"- {p}" for p in report["noindex"][:20]]
    if "links" in report:
        L += ["", f"## External links: {report['links']['checked']} checked, {len(report['links']['failing'])} failing", ""]
        L += [f"- {f['url']} → {f['status']}" for f in report["links"]["failing"]] or ["All answered."]
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Obsolescence radar for janaka.me (read-only).")
    ap.add_argument("--links", action="store_true", help="check external links (network)")
    ap.add_argument("--json", action="store_true", help="print JSON instead of markdown")
    ap.add_argument("--today", help="YYYY-MM-DD, defaults to today")
    args = ap.parse_args(argv)
    today = _date(args.today) or datetime.date.today()
    report = {
        "today": today.isoformat(),
        "watchlist": watchlist(today),
        "stale_years": stale_years(today),
        "pins": action_pins(),
        "noindex": noindex_pages(),
    }
    if args.links:
        report["links"] = link_report()
    print(json.dumps(report, ensure_ascii=False, indent=1) if args.json else render_markdown(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
