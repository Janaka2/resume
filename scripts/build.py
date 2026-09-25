#!/usr/bin/env python3
"""Regenerate every derived file of janaka.me, in dependency order.

    python3 scripts/build.py           regenerate
    python3 scripts/build.py --check   regenerate, then fail if anything changed
                                       (CI: the committed files must be current)

Order matters: the hub is inlined first, structured data is written into the
pages, the content index reads the pages, and the sitemap, feed, JSON and
llms.txt read the index. gen-og-image.py is not part of the build (needs Pillow,
only after theme token changes); the Academy page generators under
scripts/generators/ read sibling repositories and are run by hand.
"""
import os
import runpy
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import site_lib  # noqa: E402

STEPS = [
    "build-hub.py",
    "gen-structured-data.py",
    "gen-content-index.py",
    "gen-sitemap.py",
    "gen-feed.py",
    "gen-public-data.py",
]
DERIVED = ["index.html", "sitemap.xml", "feed.xml", "llms.txt", "llms-full.txt",
           "assets/content-index.json", "api/public/v1", "academy", "blog", "lab", "ai",
           "products", "resume"]


def changed_files():
    out = subprocess.run(["git", "-c", "core.quotePath=false", "status", "--porcelain", "--"] + DERIVED,
                         cwd=site_lib.ROOT, capture_output=True, text=True, encoding="utf-8").stdout
    return sorted(line[3:] for line in out.splitlines())


def main():
    check = "--check" in sys.argv
    before = changed_files() if check else []
    for step in STEPS:
        t = time.time()
        sys.argv = [step]
        runpy.run_path(os.path.join(HERE, step), run_name="__main__")
        print(f"  ({step} {time.time() - t:.1f}s)")
    if check:
        after = [f for f in changed_files() if f not in before]
        if after:
            print("\nDerived files were stale; commit the regenerated versions:", file=sys.stderr)
            for f in after:
                print("  " + f, file=sys.stderr)
            sys.exit(1)
        print("derived files are current")


if __name__ == "__main__":
    main()
