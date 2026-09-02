#!/usr/bin/env python3
"""Regenerate sitemap.xml from the pages actually on the site.

The site has no build step, so this is run by hand after adding or removing
pages:  python3 scripts/build_sitemap.py

Skipped: partials (fragments, not pages), the print-only CV template, anything
still holding a generator placeholder, and directories that are not served.
"""
import datetime, pathlib, re, subprocess
from urllib.parse import quote

SITE = 'https://janaka.me/'
SKIP_DIRS = ('partials/', 'reports/', 'chatbot/', 'ai/mcp-agent-skeleton/', 'scripts/')
# The visual CV sits in partials/ but is a real page, linked from the hub.
KEEP = ('partials/janaka_visual_resume_v3_3.html',)
SKIP_FILES = ('resume-26-3-2026.html', '404.html')
PLACEHOLDER = ("Add today's learning notes here", "Replace with the day's work")
# Redirect stubs left at renamed URLs are not pages to index.
REDIRECT = 'http-equiv="refresh"'


def last_modified(path):
    """Last commit date, falling back to the file's mtime when git is unavailable
    (a shallow CI checkout, or a work tree git declines to read)."""
    try:
        out = subprocess.run(['git', 'log', '-1', '--format=%cs', '--', path],
                             capture_output=True, text=True, timeout=10).stdout.strip()
        if re.fullmatch(r'\d{4}-\d{2}-\d{2}', out):
            return out
    except Exception:
        pass
    return datetime.date.fromtimestamp(pathlib.Path(path).stat().st_mtime).isoformat()


def main():
    root = pathlib.Path('.')
    urls = []
    for p in sorted(root.rglob('*.html')):
        f = p.as_posix()
        if (any(f.startswith(d) for d in SKIP_DIRS) and f not in KEEP) or f in SKIP_FILES:
            continue
        text = p.read_text(encoding='utf-8', errors='ignore')
        if any(ph in text for ph in PLACEHOLDER) or REDIRECT in text:
            continue
        loc = SITE + quote(f)
        if loc.endswith('/index.html'):
            loc = loc[:-len('index.html')]
        depth = f.count('/') - (1 if f.endswith('index.html') else 0)
        prio = max(0.3, round(1.0 - 0.15 * depth, 2))
        urls.append((loc, last_modified(f), prio))

    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, date, prio in urls:
        out.append('  <url>')
        out.append('    <loc>' + loc + '</loc>')
        if date:
            out.append('    <lastmod>' + date + '</lastmod>')
        out.append('    <priority>' + str(prio) + '</priority>')
        out.append('  </url>')
    out.append('</urlset>')
    pathlib.Path('sitemap.xml').write_text('\n'.join(out) + '\n', encoding='utf-8')
    print('sitemap.xml: ' + str(len(urls)) + ' urls')


if __name__ == '__main__':
    main()
