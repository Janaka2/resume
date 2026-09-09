---
name: fill-academy
description: Batch-fill empty auto-generated Janaka Academy daily pages with real content, oldest first, keeping the generated chrome and file names intact. Argument: number of pages (default 5) or a specific file path.
---

# Fill academy scaffolds

1. List scaffolds: `grep -l "Add today's learning notes here\|Replace with the day's work" academy/modules/*/FSE/*.html | sort`.
2. Take the first N (or the given file). For each, read sibling pages with the same topic slug (`ls academy/modules/*/FSE/*-<topic>.html`) and their `<h1>`s, so the new page covers a sub-topic not yet written.
3. Delegate each page to the `content-writer` agent with: file path, topic slug, list of sibling H1s to avoid, and the instruction to replace only the placeholder sections (What I learned / Key commands / Practical takeaways, or the note sections) while keeping `<title>`, canonical, chrome and footer as generated. Run up to five in parallel.
4. After each returns, verify: no placeholder text remains, exactly one H1, file still contains `site-nav.html` include and both stylesheet links.
5. Update the `<title>` and `<h1>` to the specific sub-topic if the writer chose one, keeping the date suffix pattern `TITLE - YYYY-MM-DD` in the title.
6. Commit as `Fill academy pages: <dates>` with the standard trailers.
