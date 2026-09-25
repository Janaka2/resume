---
name: standards-refresh
description: Check the current official state of an evolving standard before janaka.me depends on it - WebMCP, Google Search and AI-feature guidance, Schema.org types, llms.txt, Claude Code configuration (skills, agents, rules, hooks, settings). Compares the official documentation with the repository's implementation and changes only what is justified. Use before modifying any of these, or quarterly.
argument-hint: "webmcp | search | schema | llms | claude-code | all"
---

# Standards refresh

Prefer official sources over blogs. Record what you checked and when.

| Topic | Official sources | Repository implementation |
|---|---|---|
| WebMCP | https://webmachinelearning.github.io/webmcp/ , https://github.com/webmachinelearning/webmcp , https://developer.chrome.com/docs/ai/webmcp | `assets/js/agent/webmcp.js` (header states the checked API), `docs/ai/webmcp.md` |
| Google Search | https://developers.google.com/search/docs (fundamentals, AI features, sitemaps, canonicalization, structured data guidelines) | `scripts/gen-structured-data.py`, `scripts/gen-sitemap.py`, page heads, `robots.txt` |
| Schema.org | https://schema.org (Person, ProfilePage, WebSite, BreadcrumbList, TechArticle, SoftwareApplication, SoftwareSourceCode) | generated block + hand-written Article blocks |
| llms.txt | https://llmstxt.org | `scripts/gen-public-data.py` `render_llms` |
| Claude Code | https://code.claude.com/docs (memory/CLAUDE.md imports, `.claude/rules`, skills, sub-agents, hooks, settings) | `CLAUDE.md`, `.claude/**`, `scripts/hooks/` |

## Workflow

1. Fetch the sources for the requested topic. Note the spec version or date.
2. Compare with the implementation: API shape, required fields, deprecated patterns, new guidance.
3. Classify each difference: **breaking** (our code will stop working), **deprecated** (works, should move),
   **optional** (new capability), **noise** (trend, not a standard).
4. Change only breaking and deprecated items, inside their adapter (for WebMCP: `webmcp.js` only; for structured data:
   the generator). Do not chase optional items without a user benefit; list them instead.
5. Update the "checked on" dates in `webmcp.js` and the relevant `docs/` page, and the item's `checked` date in
   `content/watchlist.json` (add an item if the dependency is new; never remove one). Run the `verify` skill.

## Done when

A short report exists (in the reply, or `reports/standards-YYYY-MM-DD.md` if asked) with source links, the
classification, what changed and what was deliberately left.
