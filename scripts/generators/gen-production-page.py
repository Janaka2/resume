#!/usr/bin/env python3
"""Generate academy/production-ready-spring-angular/index.html from the AssetCare repository's docs/academy/ARTICLE.md.

The Markdown in the blueprint repository is canonical; this script renders it onto the Academy study skeleton with
md2academy.py (which also resolves `<!-- include: @content/... -->` blocks such as the system assembly board).
Usage: python3 scripts/generators/gen-production-page.py [path/to/ARTICLE.md]
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from md2academy import build  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_CANDIDATES = [os.path.join(os.path.dirname(ROOT), "spring-angular-production-blueprint"),
               os.path.expanduser("~/dev/spring-angular-production-blueprint")]
SRC = sys.argv[1] if len(sys.argv) > 1 else next((os.path.join(c, "docs", "academy", "ARTICLE.md") for c in _CANDIDATES
                                                 if os.path.exists(os.path.join(c, "docs", "academy", "ARTICLE.md"))), "ARTICLE.md")
OUT = os.path.join(ROOT, "academy", "production-ready-spring-angular", "index.html")
REPO = "https://github.com/Janaka2/spring-angular-production-blueprint"
CFG = {
    "title": "From CRUD to production: Angular + Spring Boot, served as a seven-course meal",
    "h1": "From CRUD to production.",
    "description": ("AssetCare, a complete Angular 22 + Spring Boot 4.1 reference application built in the open: architecture, "
                    "PostgreSQL migrations, a production API, the SPA, tests and scans, observability, Helm, K3s on a free OCI "
                    "machine and CI/CD. Every course says why, what, how, and what proves it."),
    "url": "https://janaka.me/academy/production-ready-spring-angular/",
    "badges": ["Angular 22 · Spring Boot 4.1 · Java 25", "PostgreSQL 18 · Keycloak 26", "Helm · K3s · OCI free tier", "Interactive system assembly", "Verified build, honest report"],
    "actions": [("Start at the beginning", "#before-we-sit-down"), ("See the system assembled", "#the-whole-picture-assembled-step-by-step"), ("Get the repository ↗", REPO)],
}
EXTRA = f"""
<!-- eyebrow: Reference -->
## Where to go next.

- [The repository]({REPO}): README with the run, test and deploy commands and the verification report.
- [The architecture decision records]({REPO}/tree/main/docs/adr), one per constraint you will meet.
- [Production gaps]({REPO}/blob/main/docs/PRODUCTION-GAPS.md): what the free reference does not do, and what an enterprise replaces.
- [Environment setup from zero]({REPO}/blob/main/docs/ENVIRONMENT-SETUP.md) and the [plain-language operations guide]({REPO}/blob/main/docs/operations/OPERATIONS-GUIDE.md).
- On this site: [the Spring ecosystem and Spring AI](/academy/modules/2026/FSE/spring-ecosystem-and-spring-ai.html), [Java release by release](/academy/modules/2026/FSE/java-evolution-8-to-27.html), [MCP end to end](/academy/modules/2026/FSE/mcp-end-to-end.html) and [Claude Code configuration, top down](/academy/modules/2026/FSE/claude-code-configuration.html).

> **Cook it yourself** Clone the repository, run the four commands, log in as alice, and change the first decision you disagree with. The ADR tells you what breaks.
"""
build(CFG, SRC, OUT, extra_md=EXTRA)
