#!/usr/bin/env python3
"""Render a curated Markdown source onto the Janaka Academy study skeleton.

Markdown dialect (deliberately small):
  # Title                      ignored (title comes from the page config)
  <!-- lede -->  + next line   the hero lede
  <!-- eyebrow: X -->          eyebrow for the next ## section
  ## Section / ### Sub         sections (each ## = one <section class="sec">)
  paragraphs, - lists, 1. lists, | tables |, ```lang fences
  ```flow  ... ```             an ASCII diagram in a .msgflow box
  ```html  ... ```             raw HTML passthrough
  <!-- include: file.html -->  paste a file next to the source verbatim (interactive blocks)
  > **Label** text             a callout; label decides the flavour:
                               big idea/keep this/remember -> key, trap/warning/limits -> warn,
                               memory hook/try -> try, anything else -> note
  ::: quiz Title               a self-check block: "- question" lines, then "Answers:" and "- answer" lines,
  :::                          rendered as <details> with the answers hidden until opened
  ::: fold Title               a folded block (details.code-fold) around whatever is inside
  :::
"""
import html, re


def inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?!\w)", r"<em>\1</em>", t)
    t = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', t)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', t)
    return t


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:48]


def flavour(label):
    l = label.lower()
    if any(k in l for k in ("big idea", "keep this", "remember", "rule", "definition")):
        return "key"
    if any(k in l for k in ("trap", "warning", "limit", "careful", "myth")):
        return "warn"
    if any(k in l for k in ("memory hook", "try", "exercise")):
        return "try"
    return ""


def render(md):
    lines = md.splitlines()
    out, i, n = [], 0, len(lines)
    lede, eyebrow, open_section = "", "", False

    def close():
        nonlocal open_section
        if open_section:
            out.append("\n      </div>\n    </div>\n  </section>\n")
            open_section = False

    while i < n:
        l = lines[i]
        if l.startswith("# "):
            i += 1
            continue
        m = re.match(r"<!-- eyebrow: (.*) -->", l)
        if m:
            eyebrow = m.group(1).strip()
            i += 1
            continue
        if l.strip() == "<!-- lede -->":
            lede = lines[i + 1].strip()
            i += 2
            continue
        if l.startswith("## "):
            close()
            h = l[3:].strip()
            out.append(
                f'\n  <section class="sec" id="{slug(eyebrow or h)}">\n    <div class="wrap">\n'
                f'      <p class="eyebrow">{html.escape(eyebrow)}</p>\n      <h2>{inline(h)}</h2>\n      <div class="prose rel-body">\n'
            )
            open_section = True
            i += 1
            continue
        if l.startswith("### "):
            out.append(f"<h3>{inline(l[4:].strip())}</h3>\n")
            i += 1
            continue
        if l.startswith("```"):
            lang = l[3:].strip()
            buf = []
            i += 1
            while i < n and not lines[i].startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            body = "\n".join(buf)
            if lang == "html":
                out.append(body + "\n")
            elif lang == "flow":
                out.append(f'<div class="msgflow">{html.escape(body)}</div>\n')
            else:
                cls = f' class="language-{lang}"' if lang else ""
                out.append(f"<pre><code{cls}>{html.escape(body)}</code></pre>\n")
            continue
        m = re.match(r"::: (quiz|fold)\s*(.*)", l)
        if m:
            kind, title = m.group(1), m.group(2).strip()
            buf = []
            i += 1
            while i < n and lines[i].strip() != ":::":
                buf.append(lines[i])
                i += 1
            i += 1
            if kind == "fold":
                inner = render_body("\n".join(buf))
                out.append(f'<details class="code-fold"><summary>{inline(title or "Show")}</summary><div class="fold-body">{inner}</div></details>\n')
            else:
                qs, ans, mode = [], [], "q"
                for b in buf:
                    if b.strip().lower().startswith("answers"):
                        mode = "a"
                        continue
                    if b.startswith("- "):
                        (qs if mode == "q" else ans).append(b[2:])
                items = "".join(
                    f"<li><p class=\"q\">{inline(q)}</p>{'<p class=\"a\">' + inline(ans[k]) + '</p>' if k < len(ans) else ''}</li>"
                    for k, q in enumerate(qs)
                )
                out.append(
                    f'<details class="quiz"><summary>{inline(title or "Check yourself")}<span class="hint">answer out loud, then open</span></summary>'
                    f"<ol>{items}</ol></details>\n"
                )
            continue
        if l.startswith("|"):
            rows = []
            while i < n and lines[i].startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            head, body = rows[0], [r for r in rows[2:]] if len(rows) > 2 else []
            out.append(
                "<table><thead><tr>" + "".join(f"<th>{inline(c)}</th>" for c in head) + "</tr></thead><tbody>"
                + "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in body) + "</tbody></table>\n"
            )
            continue
        if l.startswith("> "):
            buf = []
            while i < n and lines[i].startswith("> "):
                buf.append(lines[i][2:])
                i += 1
            text = " ".join(buf)
            m = re.match(r"\*\*(.+?)\*\*\s*(.*)", text)
            lbl, body = (m.group(1), m.group(2)) if m else ("Note", text)
            out.append(f'<div class="callout {flavour(lbl)}"><span class="lbl">{inline(lbl)}</span><p>{inline(body)}</p></div>\n')
            continue
        if re.match(r"[-*] ", l):
            buf = []
            while i < n and re.match(r"[-*] ", lines[i]):
                buf.append(lines[i][2:])
                i += 1
            out.append("<ul>" + "".join(f"<li>{inline(b)}</li>" for b in buf) + "</ul>\n")
            continue
        if re.match(r"\d+\. ", l):
            buf = []
            while i < n and re.match(r"\d+\. ", lines[i]):
                buf.append(re.sub(r"^\d+\. ", "", lines[i]))
                i += 1
            out.append("<ol>" + "".join(f"<li>{inline(b)}</li>" for b in buf) + "</ol>\n")
            continue
        if l.strip() == "":
            i += 1
            continue
        if l.startswith("<") and not l.startswith("<!--"):
            # raw HTML block: pass through until a blank line
            buf = []
            while i < n and lines[i].strip() != "":
                buf.append(lines[i])
                i += 1
            out.append("\n".join(buf) + "\n")
            continue
        buf = []
        while i < n and lines[i].strip() and not re.match(r"(#|```|\||> |[-*] |\d+\. |<!--|::: )", lines[i]):
            buf.append(lines[i].strip())
            i += 1
        out.append(f"<p>{inline(' '.join(buf))}</p>\n")
    close()
    return lede, "".join(out)


def render_body(md):
    """Render a fragment without section wrappers (used inside folds)."""
    _, body = render("<!-- eyebrow: x -->\n## x\n" + md)
    body = body.split('<div class="prose rel-body">\n', 1)[1]
    return body.rsplit("\n      </div>\n    </div>\n  </section>\n", 1)[0]


def page(cfg, lede, body):
    t, d = html.escape(cfg["title"]), html.escape(cfg["description"], quote=True)
    badges = "".join(f'<span class="badge{" hot" if k == 0 else ""}">{html.escape(b)}</span>\n        ' for k, b in enumerate(cfg["badges"]))
    actions = "".join(
        f'<a class="btn{" primary" if k == 0 else ""}" href="{html.escape(h)}"{" target=\"_blank\" rel=\"noopener\"" if h.startswith("http") else ""}>{html.escape(lbl)}</a>\n        '
        for k, (lbl, h) in enumerate(cfg["actions"])
    )
    return f'''<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{t} | Janaka Academy</title>
  <meta name="description" content="{d}">
  <link rel="canonical" href="{cfg["url"]}">
  <link rel="alternate" type="application/atom+xml" title="Janaka Premathilaka" href="/feed.xml">
  <meta property="og:title" content="{t} | Janaka Academy">
  <meta property="og:description" content="{d}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{cfg["url"]}">
  <meta property="og:image" content="https://janaka.me/assets/og/academy.png">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{t} | Janaka Academy">
  <meta name="twitter:description" content="{d}">
  <meta name="twitter:image" content="https://janaka.me/assets/og/academy.png">
  <link rel="icon" type="image/png" sizes="32x32" href="/assets/icons/favicon-32.png?v=1">
  <link rel="icon" type="image/png" sizes="16x16" href="/assets/icons/favicon-16.png?v=1">
  <link rel="apple-touch-icon" sizes="180x180" href="/assets/icons/apple-touch-icon.png?v=1">

  <!-- Apply the stored theme before first paint to avoid a flash -->
  <script>
    (function(){{
      try {{
        var t = localStorage.getItem("jp-theme");
        if (t === "dark" || (!t && window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches)) {{
          document.documentElement.setAttribute("data-theme", "dark");
        }}
      }} catch (e) {{}}
    }})();
  </script>

  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="preload" as="style" href="https://fonts.googleapis.com/css2?family=Archivo:wght@600;700;800&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
  <link href="https://fonts.googleapis.com/css2?family=Archivo:wght@600;700;800&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet" media="print" onload="this.media='all'">
  <noscript><link href="https://fonts.googleapis.com/css2?family=Archivo:wght@600;700;800&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet"></noscript>
  <link rel="stylesheet" href="/assets/css/theme.css?v=20260916">
  <link rel="stylesheet" href="/assets/css/subsite.css?v=20260916b">
  <link rel="stylesheet" href="/assets/css/study.css?v=20260921b">
  <link rel="manifest" href="/assets/site.webmanifest">
  <meta name="referrer" content="strict-origin-when-cross-origin">
</head>
<body class="study">
<a class="skip" href="#main">Skip to content</a>

<div data-include="/partials/site-nav.html"></div>

<main id="main">
  <section class="sec subhero">
    <div class="wrap">
      <p class="eyebrow"><a href="/academy/" style="color:inherit;text-decoration:none">&larr; Janaka Academy</a></p>
      <h1>{html.escape(cfg["h1"])}</h1>
      <p class="lede">{inline(lede)}</p>
      <div class="badges">
        {badges}</div>
      <div class="actions">
        {actions}</div>
    </div>
  </section>
{body}
</main>

<footer class="sitefoot">
  <div class="wrap">
    <span>&copy; <span id="year"></span> Janaka Academy &middot; Zug 🇨🇭</span>
    <span><a href="/academy/">Academy</a> &middot; <a href="/ai/">AI</a> &middot; <a href="/">janaka.me</a></span>
  </div>
</footer>

<script src="/assets/js/includes.js?v=20260910"></script>
<script src="/assets/js/site-nav.js?v=20260910"></script>
<script src="/assets/js/study.js?v=20260916"></script>
</body>
</html>
'''


def build(cfg, src, out):
    import os
    md = open(src, encoding="utf-8").read()
    # <!-- include: file.html --> pastes a file (relative to the source) verbatim, for interactive blocks
    md = re.sub(
        r"<!-- include: ([^\s]+) -->",
        lambda m: "```html\n" + open(os.path.join(os.path.dirname(src), m.group(1)), encoding="utf-8").read().rstrip("\n") + "\n```",
        md,
    )
    lede, body = render(md)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    html_page = page(cfg, lede, body)
    open(out, "w", encoding="utf-8").write(html_page)
    print(f"wrote {out} ({len(html_page)//1024} KB, {html_page.count('<section')} sections)")
