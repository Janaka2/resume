---
paths:
  - "content/**"
  - "partials/**"
  - "resume/**"
  - "blog/**"
  - "academy/**"
  - "lab/**"
  - "products/**"
  - "ai/index.html"
  - "chatbot/config.py"
---

# Content rules

- Facts come from the repository: `content/profile.json`, `content/projects.json`, the CV partials
  (`partials/experience.html`, `certifications.html`, `education.html`) and `.claude/skills/brand-voice/SKILL.md`.
  Never invent roles, dates, clients, certificates, metrics, testimonials or contact details. Missing fact → keep
  the current text and flag it.
- Change a fact once at its source (see the table in `AGENTS.md`), then `python3 scripts/build.py`.
- A project or product appears in `content/projects.json`, `partials/side-projects.html` and, for products,
  `products/index.html` with an `<article class="card listing" id="<slug>">`; `validate-site.py --only sync` checks
  all three agree.
- Career facts also live in `resume/index.html`, `cv/print/index.html` (PDF source), the DE dictionary in
  `assets/js/i18n.js` and `chatbot/config.py`. Update every copy in one change (the `content-guardian` agent's job).
- New hub copy needs a `data-i18n` key and a German entry (`i18n-add` skill).
- A page gets a real meta description (≤ ~160 chars) written from its own content, a canonical URL, one `<h1>`.
- Near-duplicate page? Do not copy; link. If duplicates exist, list them under `aliases` in `content/site.json`.
- Blog and case-study Article JSON-LD is hand-written: author and publisher are
  `{"@type":"Person","@id":"https://janaka.me/#me","name":"Janaka Premathilaka","url":"https://janaka.me/"}`.
- Voice: calm, concrete, evidence over adjectives, no exclamation marks (brand-voice skill).
