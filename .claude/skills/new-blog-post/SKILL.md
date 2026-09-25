---
name: new-blog-post
description: End-to-end workflow to publish a blog post on janaka.me/blog - draft in the brand voice, create the page on the design system, add the card to the blog index, set Article JSON-LD, and produce the LinkedIn teaser. Use when asked to write or publish a post. Argument: the topic or working title.
---

# Publish a blog post

Load `brand-voice` and `site-page` first.

1. **Slug and file.** `blog/posts/<kebab-slug>.html`. Check `ls blog/posts` for collisions and related posts to link.
2. **Draft** using the sub-site skeleton. Section is `blog`, eyebrow link `/blog/`. 900-1600 words, code in `<pre><code>`, close with "Practical takeaways".
3. **Structured data.** Add to `<head>`:
   ```html
   <script type="application/ld+json">
   {"@context":"https://schema.org","@type":"Article","headline":"TITLE","datePublished":"YYYY-MM-DD","dateModified":"YYYY-MM-DD","author":{"@type":"Person","@id":"https://janaka.me/#me","name":"Janaka Premathilaka","url":"https://janaka.me/"},"mainEntityOfPage":"https://janaka.me/blog/posts/SLUG.html"}
   </script>
   ```
4. **Index card.** In `blog/index.html`, find the posts grid and insert a card newest-first, matching the existing card markup exactly (copy the top card, change title, date, teaser, href `./posts/SLUG.html`). Every existing post must be listed; if one is missing, add it too.
5. **Cross-links.** Link to one or two related posts and, where relevant, to `/lab/` or `/ai/`.
6. **Derive and verify.** `python3 scripts/build.py` (adds the generated JSON-LD block, content index, sitemap, feed, llms.txt, public JSON; the post needs no manual listing anywhere else), then `python3 scripts/validate-site.py`. Preview with `python3 -m http.server 8000`: `/blog/` and the post, both themes, phone width, no console errors.
7. **Teaser.** Output a two-line LinkedIn teaser and hand off to the `social-promoter` agent if a full post is wanted.
8. **Commit** the post, `blog/index.html` and the regenerated files together as `Add blog post: TITLE`.
