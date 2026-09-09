# janaka.me improvement proposal — 9 September 2026

Prepared from a code scan plus four agent audits (site health, brand, SEO, product positioning). Nothing in this document has been applied yet.

## Where the site stands

The hub is strong: one headline, disciplined voice, a working EN/DE switch, and three shipped products that most senior engineers cannot show. The foundation underneath it has cracked in three places:

| Problem | Size | Why it matters |
|---|---|---|
| Daily academy pages are orphaned | 187 pages unlinked, 197 still empty templates | A visitor who finds the Academy sees a promise with nothing behind it |
| RepeatCycle is invisible on janaka.me | Hub says "Two products"; CV, chatbot, README and JSON-LD say nothing | The newest product, the strongest solo-execution proof, is not on the site that sells you |
| The CV page contradicts the hub | "Senior Full-Stack Java Engineer", "21+ years" vs "Senior Java Engineer & Solution Architect", "22+" | Recruiters read the CV page most carefully and see the weakest claim |

Health counts: 11 broken internal links, 5 failing external links, 6 of 6 landing pages without Open Graph tags, no `og:image` asset anywhere, no `sitemap.xml` or `robots.txt`, 9 missing German keys on the hub, 3 heading-level skips, 2 blog posts that are 8-byte stubs.

## 1. Bring RepeatCycle into the ecosystem

**Positioning.** "RepeatCycle — remembers what repeats, learns the rhythm from your own history, on your device or your own Drive." It sits beside nüchtern (makes the biology visible) and Daily Momentum (records where the day went).

**Hub changes** in `partials/side-projects.html` and the DE dictionary:
- Switch the grid from `.cards2` to `.cards3` (already defined in theme.css).
- Add a third card with keys `p3Sub`, `p3Desc`, `p3Pts`, `p3Chips`, `p3Btn`. The product-marketer agent drafted EN and DE copy; it deliberately avoids "on-device only" because Drive-first mode makes that untrue, and uses an "EN" chip because the UI is English only.
- Rewrite `pjH2` to "Three products, idea to production." and `pjLede` to "...records stay on the user's own device, or in storage the user owns." Update `pjHowP`, `pjHowPts`, `pjAcqH`, `pjAcqP`, which all still say "both" or "either".

**Everywhere else:** add a "Three shipped products" case-study card to `cv/index.html`; add the three products to the chatbot system prompt boundaries and to its grounding data so it can answer "what have you shipped yourself?"; add `SoftwareApplication` entries for all three apps to the hub JSON-LD; update the README tagline and `.claude/skills/brand-voice/SKILL.md` so future audits stop re-flagging this.

**Naming decision (yours).** The app is called RepeatCycle but lives at loop.janaka.me, and the manifest description says a third thing. Both agents flagged it. Options: register repeatcycle.app and redirect the subdomain, which keeps the acquisition promise of "source, brand, domain" honest; or rename the app to Loop, which is shorter and matches the address. Either works. Two names for one product does not. Until decided, always write "RepeatCycle · loop.janaka.me", name first.

## 2. Fix the foundation (one working session)

1. **Workflow bug.** `daily_learning_generator.yml` line 226 tests `"<ul>" in block`; the year page has `<ul class="grid">`, so the "left alone" branch runs every day. Change to a regex on `<ul\b` and backfill the 187 missing links in one script. This alone reconnects most of the Academy.
2. **Broken links.** Lab "Open demo" buttons to `rag-demo/`, `job-agent/`, `momentum/` (folders do not exist); academy favicons pointing at a non-existent icon set; two missing images in the Java modernisation pages; one `httpsfs://` typo; the job-research-agent GitHub link returns 404.
3. **CV page facts.** Title, description and two body lines to "Senior Java Engineer & Solution Architect" and "22+".
4. **Blog stubs.** `rag-faiss-patterns.html` and `spring-kafka-deadletter.html` contain the word "progress". Finish them or delete them; either way they must not ship as-is.
5. **German gaps.** Nine hub keys have no DE entry (four journey tabs, five language-level labels). The visual CV's own dictionary is missing 24 of 74 keys.
6. **Heading skips** on blog, lab and ai landing pages (h1 straight to h3 in card grids).

## 3. Discoverability

- Create one 1200x630 `og:image` and add the full OG plus `twitter:card` block to the six landing pages; add canonical to the hub.
- Adopt the six title and description rewrites from the SEO audit. They add role and location where recruiters search and stay within limits.
- Generate `sitemap.xml` and `robots.txt`. Decide what to do with `academy/modules/2025`, which mirrors most of 2026 file for file and currently self-canonicalises as duplicate content.
- Resolve the double URLs. Every property answers at both `blog.janaka.me` and `janaka.me/blog/`. Canonical tags choose the path form, but the lab page links the subdomain form. Pick one, redirect the other.
- Add `Article` JSON-LD to the three real blog posts.

## 4. Academy: from a pile to a curriculum

The two bots have produced 258 pages in 2026, of which 197 are still empty. Proposed sequence: fix the linking bug first, then fill the oldest scaffolds with `/fill-academy` in batches of five so each new page covers a sub-topic its siblings have not, then re-head the 200 older pages onto the shared chrome with a one-shot script (63 still load the legacy stylesheet). After that, group filled pages into the three learning paths already promised on the Academy landing page. Consider changing the bot to scaffold only when yesterday's page was filled; an empty page every day is a liability, not content.

## 5. Bigger moves worth considering

- **A Products property.** Three privacy-first PWAs deserve `/products/` on the site-nav alongside Blog, Lab, AI, CV and Academy: one page per app with the story, screenshots, the privacy model and the acquisition terms. Today they are a section halfway down the hub.
- **A "built with AI in the loop" case study.** The paragraph on the hub about how the products were built is the most differentiating claim on the site for a 2026 hiring manager. Turn it into a full page with the actual workflow, the review discipline and what the model got wrong.
- **Hub navigation to the properties.** The hub's top bar only scrolls to sections; the sub-sites are reachable only from the footer. Add Blog, Lab, AI and Academy links to the hub nav, or a single "More" entry.
- **Lab demos that run.** Three demo buttons lead nowhere. Either host the demos as static pages under `lab/`, or relabel the buttons "Source on GitHub".
- **Rename "Momentum Journal"** in the lab so it stops colliding with Daily Momentum.
- **Trim the mission prose in the hero.** "Core values" and "the giant within a thousand hearts" read as a poster; one line plus the Academy link keeps the voice.

## Roadmap

| When | Work | Outcome |
|---|---|---|
| This week | Section 2 items 1–4, RepeatCycle card and lede, brand-voice skill update | Site factually correct, Academy reconnected, three products visible |
| Weeks 2–4 | Section 3 (OG image, meta, sitemap, URL canonicalisation), remaining Section 1 items (CV card, chatbot, JSON-LD), German gaps | Every property previews well when shared and is indexed once |
| Quarter | Section 4 batches, Products property, AI-in-the-loop case study, hub nav | Academy is a curriculum; products are a first-class property |

## Decisions needed from you

1. RepeatCycle name and domain: keep both names, buy repeatcycle.app, or rename to Loop?
2. The two blog stubs: finish or delete?
3. Sub-site URLs: path form (`janaka.me/blog/`) or subdomain form (`blog.janaka.me`) as canonical?
4. Academy 2025 duplicate folder: redirect to 2026, or keep and exclude from the sitemap?
5. Products as a new property on the nav: yes or not yet?

Everything in Sections 1 to 3 can be executed by the existing agents through `/weekly-brand-review` once the decisions above are made.
