# Night scan — 10 September 2026

Five reviewers went over the whole site from different angles: visitor journeys, technical quality, learning content, the AI assistant, and market growth. I verified the headline numbers myself before ranking. Everything below is a proposal; nothing has been applied.

## Facts established tonight

| Finding | Verified |
|---|---|
| Daily academy pages: 199 exist, 0 filled. Every one still carries the template text. 259 academy URLs are in the sitemap, most of them empty. | grep count |
| The blog post on MCP opens with "Multi-capability prompts". MCP is the Model Context Protocol. The hub claims MCP experience. | file read |
| `cv/index.html` states "40+ enterprise projects", "≈30% avg performance gain", "3,000+ daily users", CKA 2024 and AWS Solutions Architect 2023. None of these appear in the hub's experience or certification partials. | grep |
| The hero portrait is 1760×2264 px and 539 KB, displayed at 172 px. The "SVG" favicon is a 287 KB base64 PNG fetched on every page. Two unreferenced 6 MB PNGs and six unreferenced 1 MB icons sit in the repo. | file sizes |
| The chat assistant runs through two nested iframes (janaka.me → github.io/pa → Hugging Face). Its Gradio API is public with no rate limit and an admin login that defaults to "change-me". The prompt rewritten in this repo on 9 Sept is not what is deployed. | curl, code read |
| Two blog posts ask visitors for their own Gemini API key. The evals post cites a LangChain API that does not exist. | file read |
| No 404 page, no site manifest, no RSS feed, no search, no cross-links between blog, academy and lab. | file listing |

## The ranked list

Effort: S = under two hours, M = half a day to a day, L = several days. Impact is against the vision in `goals/vision.md`: career first, product sales second, academy third.

### Tier 1 — credibility and safety. Do these first.

**1. Fix the MCP post and the AI page definition.** (S, career)
Rewrite `blog/posts/mcp-agent-integration.html` around the real protocol: servers, tools, resources, transports, one worked server example, and link the unreferenced `ai/mcp-agent-skeleton/`. The single most damaging page for an AI-literate hiring manager to find.

**2. Make `/cv/` tell the hub's story.** (M, career)
Rebuild the CV page from `partials/experience.html` and `certifications.html`. Delete every figure and certification that cannot be evidenced, or add the evidence to the hub first. A recruiter who reads both pages today stops trusting either. The `cv-sync` agent enforces this afterwards.

**3. Lock down the chatbot.** (S, safety)
`show_api=False`, a queue with concurrency limits, `secrets.compare_digest` for the admin login, refuse to start on the default password, a per-IP rate limit on the answer endpoint, and a `requirements.txt` plus a deploy workflow so the repo and the Hugging Face Space stop drifting. Closes an OpenAI credit drain and a trivial admin takeover.

**4. Stop the empty-page machine and quarantine what it made.** (S then M, SEO)
Generator exits when yesterday's page is unfilled; disable the daily-note workflow entirely (11 notes, 0 filled); scaffold template gets `noindex`; sitemap generator skips placeholder pages; the 199 scaffolds are removed from the year page and the log. Google is currently indexing 199 thin duplicates against the domain.

**5. Cut page weight by roughly 800 KB.** (S, all)
Portrait resized to 344×443 WebP with JPG fallback and `width/height` on both pages; favicon replaced with a true 1 KB vector or the PNG links alone; unreferenced 6 MB and 1 MB images deleted; Google Fonts loaded non-blocking or self-hosted with `font-display: swap`.

### Tier 2 — conversion. These turn visits into email.

**6. An availability line and a "Work with me" page.** (S, career)
One line under the hero badges: open to permanent or contract, pensum, radius, notice period. A `/work/` page with four rows: permanent, contract, fractional architect, AI-in-regulated-systems advisory, plus mentoring tied to the Academy, ending in one ask. Needs from you: contract terms, notice, earliest start.

**7. Three STAR case studies from the banking work.** (M, career)
The merger migration with zero operational interruptions, the master-data golden source, and agentic RAG inside the perimeter. Each: situation, task, action, result, stack. Replace the GitHub-demo "case studies" on `/cv/`. Needs from you: team sizes, volumes, timelines, what is disclosable.

**8. Product proof on `/products/`.** (S once supplied, sales)
One phone screenshot per listing in light and dark, a dated "What changed" list per product, and a forwardable catalogue PDF generated from the page with print CSS. Buyers forward before they decide. Needs from you: four screenshots and release dates.

**9. Chat assistant that opens instantly and never shows a black box.** (M, all)
Drop the middle iframe, warm the Space on hover, show a "waking up" skeleton with email fallback after 45 seconds. Then the lean replacement: a static FAQ answered client-side inside the existing modal, and a single serverless function calling Claude Haiku with prompt caching for everything else. Per-page context so `/products/` opens in "ask about this product" mode, and a recruiter mode covering notice, hybrid policy and authorisation. Leads to a webhook instead of a CSV that dies on rebuild.

**10. A position page: "AI inside the perimeter".** (M, career)
Five or six numbered positions on shipping AI in a bank, each backed by CV evidence, with the "built with AI in the loop" workflow as personal proof. The page that answers the vision's "go-to architect" claim and gives every LinkedIn post a link.

### Tier 3 — make the ecosystem coherent and easy to live with

**11. Pre-assemble the hub at commit time.** (M, technical)
A build script inlines the partials into `index.html` while keeping partials as source; the loader skips inlined slots. Instant first paint, correct previews from bots that do not run JavaScript, and the German version can be emitted as `/de/` with proper `hreflang` from the same step.

**12. Real learning paths instead of a wall of empty days.** (M, academy)
Three ordered paths under `academy/paths/`: Java backend for regulated systems, Linux for incidents, practical AI in Java. Each an ordered list with per-step checkboxes persisted locally and a progress bar. Replace "Choose your path" with them. Merge the 2025 folder into 2026. Rewrite the Academy landing copy to brand voice and delete promises that are not yet true: mentorship channels, contributing guide, twelve-month programme.

**13. Content index, search, feed and cross-links.** (M, all)
One script scans blog, filled academy pages and lab into `assets/content-index.json`. That drives reading time, "updated" dates, a topics page, a `/` keyboard search overlay in the shared nav, an Atom feed at `/feed.xml`, a "Related" block on every post and module, and a `/now/` page. Rejected: a mailing list, until there is cadence and traffic to justify a provider.

**14. Accessibility and resilience pass.** (S, all)
Focus trap and `inert` background for the chat modal; real `role="tablist"` tabs with arrow keys on the Journey section; a skip link; `aria-pressed` on the theme button; light-mode secondary text darkened one step so the spec-panel labels pass AA; a `404.html` on the sub-site chrome; a site manifest; print stylesheet fixes on `/cv/`.

**15. Count visits without tracking, and align the outside.** (S, all)
GoatCounter or Cloudflare Web Analytics on janaka.me only, declared in the footer, products stay analytics-free. Per-page social images from the existing generator. A `Janaka2/Janaka2` GitHub profile README carrying the positioning line and the four products. Without this you cannot tell which page earned an interview.

### Also flagged, your call

- The Life Journey tabs publish your marriage year and your children's birth months. A public site does not need them; one line would do.
- The certifications list ends on "Remember the German Articles" and "First Aid" after the Sun Certified Enterprise Architect. Reorder, and fold the rest into a collapsed "Also completed".
- The hero Profile card still reads as template: "rock-solid", "moves the needle", "find a way or make one", "Core values". Three factual sentences would serve a Swiss senior audience better.
- The lab says "runnable" and nothing runs. Either build three vanilla-JS demos with embedded data, or relabel it "notes and source".

## Suggested order

| Week | Items | What you supply |
|---|---|---|
| This week | 1, 3, 4, 5, 14 | nothing |
| Next week | 2, 6, 9 (first half), 15 | contract terms, notice period, CV evidence |
| Weeks 3–4 | 7, 8, 10 | case-study facts, screenshots, release dates |
| Quarter | 9 (second half), 11, 12, 13 | one paragraph of review per generated page |

Items 1, 3, 4, 5, 11, 13 and 14 need no input from you and can be executed by the agents via `/weekly-brand-review` once you say go.
