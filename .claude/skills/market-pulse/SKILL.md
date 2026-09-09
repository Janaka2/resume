---
name: market-pulse
description: Monthly market-demand check for Janaka's target roles and stack - runs the market-trend-analyst agent, applies the low-risk updates (trend map, academy topic pool suggestions, meta keywords), and records the sourced findings under reports/. Use monthly or when asked what the market wants.
---

# Market pulse

1. Launch the `market-trend-analyst` agent with today's date and the current chips from `partials/contact-skills-languages.html` and `cv/index.html`.
2. Save its report verbatim to `reports/market-pulse-YYYY-MM.md` (create `reports/` if missing).
3. Apply directly:
   - Edits to `ai/research/trend-map-2026.md` (tier moves, new entries, dated "Last reviewed" line at the top).
   - Keyword additions to meta descriptions where a page is clearly about that topic (delegate to `seo-optimizer`).
4. Propose, do not apply: skill chip changes on the hub and CV, new topic-pool entries in `.github/workflows/daily_learning_generator.yml`, certifications to pursue. List each with the source that justifies it.
5. Hand five blog titles and five academy topics to the report's "Content pipeline" section.
6. Commit as `Market pulse YYYY-MM` with the standard trailers.
