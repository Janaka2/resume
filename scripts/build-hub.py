#!/usr/bin/env python3
"""Inline the hub's partials into index.html so the page paints without JavaScript.

partials/*.html stay the source of truth. Each
    <div data-include="partials/x.html"></div>
becomes
    <div data-include="partials/x.html" data-inlined>…partial…<!-- /include partials/x.html --></div>
and the loader (assets/js/includes.js) skips slots that already have content,
so the page behaves identically with or without this step. Idempotent: re-run
after any partial changes. Wired into /release-check.
"""
import re, sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HUB = os.path.join(ROOT, "index.html")

SLOT = re.compile(
    r'(?P<indent>[ \t]*)<(?P<tag>div|footer)(?P<cls> class="[^"]*")? data-include="(?P<src>partials/[^"]+)"'
    r'(?: data-inlined>.*?<!-- /include (?P=src) -->|>)</(?P=tag)>\n',
    re.S,
)

def main():
    html = open(HUB, encoding="utf-8").read()
    count = 0
    def repl(m):
        nonlocal count
        path = os.path.join(ROOT, m.group("src"))
        body = open(path, encoding="utf-8").read().rstrip("\n")
        count += 1
        cls = m.group("cls") or ""
        return (f'{m.group("indent")}<{m.group("tag")}{cls} data-include="{m.group("src")}" data-inlined>\n'
                f'{body}\n{m.group("indent")}<!-- /include {m.group("src")} --></{m.group("tag")}>\n')
    out = SLOT.sub(repl, html)
    if out != html:
        open(HUB, "w", encoding="utf-8").write(out)
    print(f"inlined {count} partials into index.html")

if __name__ == "__main__":
    main()
