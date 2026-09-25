#!/usr/bin/env python3
"""Generate sitemap.xml for janaka.me.

Run from anywhere:  python3 scripts/gen-sitemap.py   (or scripts/build.py for everything)

The URL list is content/site.json via site_lib.pages(): the listed pages plus
every *.html under the crawl roots, minus excluded paths, aliases (near-duplicates
that point their canonical elsewhere), stubs, unfilled scaffolds and noindex pages.
lastmod is the day the file last changed on main (site_lib.modified).
"""
import os
import sys
from xml.dom import minidom
from xml.sax.saxutils import escape

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import site_lib  # noqa: E402


def render(entries):
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, mod in entries:
        lines.append(f"  <url><loc>{escape(loc)}</loc><lastmod>{mod}</lastmod></url>")
    lines.append("</urlset>")
    xml = "\n".join(lines) + "\n"
    minidom.parseString(xml.encode("utf-8"))          # raises on malformed output
    return xml


def main():
    entries = [(p.url, site_lib.modified(p.rel)) for p in site_lib.pages()]
    out = os.path.join(site_lib.ROOT, "sitemap.xml")
    site_lib.write_if_changed(out, render(entries))
    print(f"sitemap.xml: {len(entries)} URLs")


if __name__ == "__main__":
    main()
