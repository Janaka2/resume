---
paths:
  - "assets/css/**"
  - "assets/js/**"
  - "partials/**"
  - "index.html"
  - "resume/index.html"
  - "**/index.html"
---

# Frontend rules

- Design system: `assets/css/theme.css` tokens only (`--bg --bg2 --tx --tx2 --ln --ac --ok --chip --shadow --r
  --font-head`); `subsite.css` after it on sub-sites; `study.css` on Academy study pages. `resume/index.html` holds a
  copy of the tokens and is the visual source of truth; keep both in sync.
- Contrast: body and small text ≥ 4.5:1 in both themes (compute it; light `--ok` was darkened to #4E7560 for this).
- Motion only to show state, ≤ 250 ms, and disabled under `prefers-reduced-motion`.
- Mobile first: check ~375px, no horizontal scroll, nothing important behind hover, tap targets ≥ 40px.
- Semantic HTML before ARIA: `header nav main section article aside footer figure time`, one `<h1>`, ordered headings,
  alt text on meaningful images, visible `:focus-visible`.
- Scripts: no new libraries, no blocking `<script>` in `<head>` except the pre-paint theme snippet; behaviour boots on
  `partials:loaded`. Optional features load lazily (as `includes.js` does for WebMCP).
- Hub partials are the source; run `python3 scripts/build-hub.py` (or `build.py`) after editing one.
- Bump `?v=` on `study.js` / `study.css` in pages and `scripts/generators/` when those files change.
- Never redesign the whole site for a component change. Big visual work: `modernize-ui` skill.
