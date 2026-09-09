---
name: site-page
description: How to create or modify any page on janaka.me so it uses the shared design system - the exact HTML skeleton, chrome checklist, design tokens, and where hub pages differ from sub-site pages. Load before writing or editing any HTML in this repo.
---

# Creating a page on the shared design system

Read `CLAUDE.md` for the architecture. This skill is the copy-paste template.

## Sub-site page skeleton (blog, lab, ai, cv, academy)

```html
<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>PAGE TITLE — Janaka Premathilaka</title>
  <meta name="description" content="ONE SENTENCE, ≤155 CHARS, ROLE + TOPIC" />
  <link rel="canonical" href="https://janaka.me/SECTION/PATH" />
  <meta property="og:title" content="PAGE TITLE" />
  <meta property="og:description" content="SAME AS DESCRIPTION" />
  <meta property="og:type" content="article" />
  <meta property="og:url" content="https://janaka.me/SECTION/PATH" />
  <meta property="og:image" content="https://janaka.me/assets/Janaka.png" />
  <meta name="twitter:card" content="summary_large_image" />

  <script>
    (function(){
      try {
        var t = localStorage.getItem("jp-theme");
        if (t === "dark" || (!t && window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches)) {
          document.documentElement.setAttribute("data-theme", "dark");
        }
      } catch (e) {}
    })();
  </script>

  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Archivo:wght@600;700;800&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="/assets/css/theme.css" />
  <link rel="stylesheet" href="/assets/css/subsite.css" />
</head>
<body>

<div data-include="/partials/site-nav.html"></div>

<main>
  <article class="sec subhero">
    <div class="wrap">
      <p class="eyebrow"><a href="/SECTION/" style="color:inherit;text-decoration:none">&larr; SECTION</a></p>
      <div class="prose">
        <h1>PAGE TITLE</h1>
        <p class="sub">DATE · TAGS</p>
        <!-- content -->
      </div>
    </div>
  </article>
</main>

<footer class="sitefoot">
  <div class="wrap">
    <span>&copy; <span id="year"></span> Janaka Premathilaka</span>
    <span><a href="/SECTION/">SECTION</a> &middot; <a href="/">janaka.me</a></span>
  </div>
</footer>

<script src="/assets/js/includes.js"></script>
<script src="/assets/js/site-nav.js"></script>
</body>
</html>
```

## Rules

- Root-absolute paths (`/assets/...`, `/partials/...`) on sub-site pages. The hub uses relative paths and its own inline nav; do not add `site-nav.html` to the hub.
- Never load `assets/css/styles.css` (legacy). Never add a page-local stylesheet; if a style is missing, add it to `subsite.css` built from tokens.
- Colours only via tokens: `--bg`, `--bg2`, `--tx`, `--tx2`, `--ln`, `--ac`, `--ok`, `--chip`, `--shadow`, `--r`. Fonts via `--font-head` and inherited body font.
- Available layout classes: `.sec`, `.wrap`, `.subhero`, `.eyebrow`, `.prose`, `.lede`, `.badges`/`.badge`, `.chips`/`.chip`, `.card`, `.cards2`, `.cta`, `.btn`/`.btn.primary`. Check `theme.css` and `subsite.css` before inventing a class.
- Exactly one `<h1>`. Headings in order.
- Images: `<img src="..." alt="..." loading="lazy">`, assets under the section's own `assets/` folder.
- Test with `python3 -m http.server 8000` in light and dark theme.

## Checklist before commit

- [ ] pre-paint theme script present
- [ ] theme.css + subsite.css linked, no styles.css
- [ ] shared nav include + footer + includes.js + site-nav.js
- [ ] title, description, canonical, og:*, twitter:card
- [ ] one H1, no hard-coded colours
- [ ] page is linked from its section index (and, for academy, the log/nav block)
