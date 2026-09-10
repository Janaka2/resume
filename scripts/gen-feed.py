#!/usr/bin/env python3
"""Generate feed.xml (Atom 1.0) for janaka.me from assets/content-index.json.

Run from anywhere:  python3 scripts/gen-content-index.py && python3 scripts/gen-feed.py
Writes <repo root>/feed.xml with the 30 newest blog, academy and lab entries.
The output is parsed back with xml.dom.minidom before it is written, so a
malformed feed never reaches the repo.
"""
import json
import os
import sys
from xml.dom import minidom
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, "assets", "content-index.json")
OUT = os.path.join(ROOT, "feed.xml")

SITE = "https://janaka.me/"
FEED_URL = SITE + "feed.xml"
TITLE = "Janaka Premathilaka"
SUBTITLE = "Clear, hands-on articles on Java, Kafka, RAG, agents and evals, plus academy modules and lab notes."
AUTHOR = "Janaka Premathilaka"
SECTIONS = ("blog", "academy", "lab")
LIMIT = 30
SECTION_LABEL = {"blog": "Blog", "academy": "Academy", "lab": "Lab"}


def stamp(day):
    """YYYY-MM-DD -> RFC 3339 timestamp Atom requires."""
    return f"{day}T00:00:00Z"


def entry_xml(e):
    link = SITE.rstrip("/") + e["url"]
    summary = e.get("description") or e["title"]
    label = SECTION_LABEL.get(e["section"], e["section"].title())
    lines = [
        "  <entry>",
        f"    <title>{escape(e['title'])}</title>",
        f'    <link rel="alternate" type="text/html" href="{escape(link)}"/>',
        f"    <id>{escape(link)}</id>",
        f"    <published>{stamp(e['date'])}</published>",
        f"    <updated>{stamp(e.get('updated') or e['date'])}</updated>",
        f'    <category term="{escape(e["section"])}" label="{escape(label)}"/>',
        f"    <summary>{escape(summary)}</summary>",
        "  </entry>",
    ]
    return "\n".join(lines)


def main():
    with open(INDEX, encoding="utf-8") as fh:
        index = json.load(fh)
    entries = [e for e in index if e.get("section") in SECTIONS]
    entries.sort(key=lambda e: (e["date"], e["url"]), reverse=True)
    entries = entries[:LIMIT]
    if not entries:
        print("no entries; run scripts/gen-content-index.py first", file=sys.stderr)
        sys.exit(1)

    feed_updated = max(e.get("updated") or e["date"] for e in entries)
    parts = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<feed xmlns="http://www.w3.org/2005/Atom">',
        f"  <title>{escape(TITLE)}</title>",
        f"  <subtitle>{escape(SUBTITLE)}</subtitle>",
        f'  <link rel="alternate" type="text/html" href="{SITE}"/>',
        f'  <link rel="self" type="application/atom+xml" href="{FEED_URL}"/>',
        f"  <id>{SITE}</id>",
        f"  <updated>{stamp(feed_updated)}</updated>",
        f"  <author><name>{escape(AUTHOR)}</name><uri>{SITE}</uri></author>",
        "  <generator>scripts/gen-feed.py</generator>",
    ]
    parts.extend(entry_xml(e) for e in entries)
    parts.append("</feed>")
    xml = "\n".join(parts) + "\n"

    minidom.parseString(xml.encode("utf-8"))   # raises on malformed output

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(xml)
    print(f"wrote {OUT}: {len(entries)} entries")


if __name__ == "__main__":
    main()
