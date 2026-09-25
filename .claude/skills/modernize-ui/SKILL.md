---
name: modernize-ui
description: Substantial visual or interaction work on janaka.me - a new section design, a page redesign, navigation, typography, spacing, responsive behaviour, motion or accessibility improvements across components. Use when asked to modernise, redesign, polish or restyle; not for one-line CSS fixes.
---

# Modernize UI

Target: professional, technical, calm, credible, fast. The portfolio of a senior engineer, not a template. Load
`site-page` for the page skeleton and `brand-voice` for any copy.

## 1. Understand before changing

- Read `assets/css/theme.css` (tokens, components), `assets/css/subsite.css`, and `resume/index.html` (the visual
  source of truth). Screenshot or describe the current state at 375px, 768px and 1280px, light and dark.
- Write down what is wrong and why (hierarchy, spacing, contrast, clutter, mobile breakage). Change only that.

## 2. Principles

- Tokens only; add a token rather than a hard-coded colour. Keep `theme.css` and `resume/index.html` tokens in sync;
  after token changes run `python3 scripts/gen-og-image.py` (needs Pillow).
- Strong typography (Archivo headings, IBM Plex Sans body, Plex Mono for code), generous but efficient spacing,
  restrained palette, subtle depth (`--shadow`), consistent radius (`--r`).
- Avoid: heavy gradients, glassmorphism, animation everywhere, giant empty heroes, stock AI illustrations, badge
  walls, carousels, tiny text, low contrast.
- Motion only for state, short, and off under `prefers-reduced-motion`.
- Mobile first; nothing important behind hover; tap targets ≥ 40px; no horizontal scroll.
- Semantic HTML and visible focus; contrast ≥ 4.5:1 for text in both themes (compute it).
- No UI framework, no new runtime library.

## 3. Verify

- Browser at three widths, both themes, EN and DE on the hub, keyboard only (Tab through the page).
- `python3 scripts/build.py` if partials changed; `python3 scripts/validate-site.py`.
- Ask `quality-guardian` to review accessibility and performance of the diff; ask `discovery-guardian` if headings,
  titles or page structure changed.

## Done when

The stated problems are fixed, nothing else moved, both themes and all widths look intentional, and the validator
is OK.
