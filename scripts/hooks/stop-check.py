#!/usr/bin/env python3
"""Claude Code Stop hook for janaka.me (wired in .claude/settings.json).

Runs when Claude is about to finish a turn. Fast (a second or two) and
deterministic; it never edits files:

  1. nothing public changed in the working tree -> exit 0 immediately
  2. pages, partials or content/*.json changed but no derived file did
     -> ask for `python3 scripts/build.py`
  3. run validate-site.py on the changed pages (meta, JSON-LD, links, data sync,
     WebMCP wiring) -> report failures

Exit 2 hands the message back to Claude as feedback (it keeps working);
exit 0 lets it stop. If the hook already blocked once this turn
(stop_hook_active) it steps aside, so it can never loop. The full suite is CI's
job (.github/workflows/site-checks.yml), not this hook's.
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SOURCES = (".html",)
SOURCE_DIRS = ("content/", "partials/")
NO_DERIVED = {"content/watchlist.json"}          # feeds the maintenance scan, not the build
DERIVED = ("sitemap.xml", "feed.xml", "llms.txt", "llms-full.txt", "assets/content-index.json", "api/public/v1/")
WATCHED_PREFIXES = ("content/", "partials/", "assets/js/", "scripts/", "robots.txt")


def changed():
    out = subprocess.run(["git", "-c", "core.quotePath=false", "status", "--porcelain", "--untracked-files=all"],
                         cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=20).stdout
    return [line[3:].split(" -> ")[-1].strip('"') for line in out.splitlines()]


def main():
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        payload = {}
    if payload.get("stop_hook_active"):
        return 0
    try:
        files = changed()
    except (OSError, subprocess.SubprocessError):
        return 0
    public = [f for f in files if f.endswith(SOURCES) or f.startswith(WATCHED_PREFIXES)]
    if not public:
        return 0

    problems = []
    sources = [f for f in public if ((f.endswith(".html") and not f.startswith(".claude/")) or f.startswith(SOURCE_DIRS))
               and f not in NO_DERIVED]
    derived = [f for f in files if f.startswith(DERIVED)]
    if sources and not derived:
        problems.append("Pages or content changed but no derived file did. Run `python3 scripts/build.py` "
                        "(sitemap, content index, feed, JSON-LD, llms.txt, api/public/v1) and include the "
                        "results, or say why this change has no discovery impact.")

    res = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "validate-site.py"), "--changed", "--quiet",
                          "--only", "meta,jsonld,links,sync,webmcp,inventory"],
                         cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=60)
    if res.returncode != 0:
        problems.append("validate-site.py found problems in the changed files:\n" + res.stdout.strip())

    if problems:
        print("janaka.me stop check\n\n" + "\n\n".join(problems), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
