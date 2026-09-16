#!/usr/bin/env python3
"""Generate academy/production-ready-spring-angular/index.html from the AssetCare repository's docs/academy/ARTICLE.md.

The Markdown in the blueprint repository is canonical; this script renders it onto the Academy study skeleton.
Usage: python3 scripts/generators/gen-production-page.py [path/to/ARTICLE.md]
"""
import html, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_CANDIDATES = [os.path.join(os.path.dirname(ROOT), "spring-angular-production-blueprint"),
               os.path.expanduser("~/dev/spring-angular-production-blueprint")]
SRC = sys.argv[1] if len(sys.argv) > 1 else next((os.path.join(c, "docs", "academy", "ARTICLE.md") for c in _CANDIDATES
                                                 if os.path.exists(os.path.join(c, "docs", "academy", "ARTICLE.md"))), "ARTICLE.md")
OUT = os.path.join(ROOT, "academy", "production-ready-spring-angular", "index.html")
URL = "https://janaka.me/academy/production-ready-spring-angular/"
TITLE = "From CRUD to production: Angular + Spring Boot, served as a seven-course meal"
DESC = ("AssetCare, a complete Angular 22 + Spring Boot 4.1 reference application built in the open: architecture, "
        "PostgreSQL migrations, a production API, the SPA, tests and scans, observability, Helm, K3s on a free OCI "
        "machine and CI/CD. Every course says why, what, how, and what proves it.")
REPO = "https://github.com/Janaka2/spring-angular-production-blueprint"

def inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', t)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', t)
    return t

def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40]

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
            i += 1; continue
        m = re.match(r"<!-- eyebrow: (.*) -->", l)
        if m:
            eyebrow = m.group(1).strip(); i += 1; continue
        if l.strip() == "<!-- lede -->":
            lede = lines[i + 1].strip(); i += 2; continue
        if l.startswith("## "):
            close(); h = l[3:].strip()
            out.append(f'\n  <section class="sec" id="{slug(eyebrow or h)}">\n    <div class="wrap">\n      <p class="eyebrow">{html.escape(eyebrow)}</p>\n      <h2>{inline(h)}</h2>\n      <div class="prose rel-body">\n')
            open_section = True; i += 1; continue
        if l.startswith("### "):
            out.append(f"<h3>{inline(l[4:].strip())}</h3>\n"); i += 1; continue
        if l.startswith("```"):
            lang = l[3:].strip(); buf = []; i += 1
            while i < n and not lines[i].startswith("```"):
                buf.append(lines[i]); i += 1
            i += 1
            cls = f' class="language-{lang}"' if lang else ""
            out.append(f"<pre><code{cls}>{html.escape(chr(10).join(buf))}</code></pre>\n"); continue
        if l.startswith("|"):
            rows = []
            while i < n and lines[i].startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")]); i += 1
            head, body = rows[0], [r for r in rows[2:]]
            out.append("<table><thead><tr>" + "".join(f"<th>{inline(c)}</th>" for c in head) + "</tr></thead><tbody>"
                       + "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in body) + "</tbody></table>\n"); continue
        if l.startswith("> "):
            buf = []
            while i < n and lines[i].startswith("> "):
                buf.append(lines[i][2:]); i += 1
            text = " ".join(buf)
            m = re.match(r"\*\*(.+?)\*\*\s*(.*)", text)
            lbl, body = (m.group(1), m.group(2)) if m else ("Note", text)
            out.append(f'<div class="callout key"><span class="lbl">{inline(lbl)}</span><p>{inline(body)}</p></div>\n'); continue
        if re.match(r"[-*] ", l):
            buf = []
            while i < n and re.match(r"[-*] ", lines[i]):
                buf.append(lines[i][2:]); i += 1
            out.append("<ul>" + "".join(f"<li>{inline(b)}</li>" for b in buf) + "</ul>\n"); continue
        if re.match(r"\d+\. ", l):
            buf = []
            while i < n and re.match(r"\d+\. ", lines[i]):
                buf.append(re.sub(r"^\d+\. ", "", lines[i])); i += 1
            out.append("<ol>" + "".join(f"<li>{inline(b)}</li>" for b in buf) + "</ol>\n"); continue
        if l.strip() == "":
            i += 1; continue
        buf = []
        while i < n and lines[i].strip() and not re.match(r"(#|```|\||> |[-*] |\d+\. |<!--)", lines[i]):
            buf.append(lines[i].strip()); i += 1
        out.append(f"<p>{inline(' '.join(buf))}</p>\n")
    close()
    return lede, "".join(out)

md = open(SRC, encoding="utf-8").read()
lede, body = render(md)
t, d = html.escape(TITLE), html.escape(DESC, quote=True)
page = f'''<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{t} | Janaka Academy</title>
  <meta name="description" content="{d}">
  <link rel="canonical" href="{URL}">
  <link rel="alternate" type="application/atom+xml" title="Janaka Premathilaka" href="/feed.xml">
  <meta property="og:title" content="{t} | Janaka Academy">
  <meta property="og:description" content="{d}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{URL}">
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
  <link rel="stylesheet" href="/assets/css/study.css?v=20260916b">
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
      <h1>From CRUD to production.</h1>
      <p class="lede">{inline(lede)}</p>
      <div class="badges">
        <span class="badge hot">Angular 22 · Spring Boot 4.1 · Java 25</span>
        <span class="badge">PostgreSQL 18 · Keycloak 26</span>
        <span class="badge">Helm · K3s · OCI free tier</span>
        <span class="badge">Verified build, honest report</span>
      </div>
      <div class="actions">
        <a class="btn primary" href="#before-we-sit-down">Start at the beginning</a>
        <a class="btn" href="{REPO}" target="_blank" rel="noopener">Get the repository ↗</a>
        <a class="btn" href="{REPO}/blob/main/README.md#verification-report" target="_blank" rel="noopener">Verification report ↗</a>
      </div>
    </div>
  </section>
{body}
  <section class="sec" id="next">
    <div class="wrap">
      <p class="eyebrow">Reference</p>
      <h2>Where to go next.</h2>
      <div class="prose rel-body">
<ul>
  <li><a href="{REPO}" target="_blank" rel="noopener">The repository</a>: README with the run, test and deploy commands and the verification report.</li>
  <li><a href="{REPO}/tree/main/docs/adr" target="_blank" rel="noopener">The architecture decision records</a>, one per constraint you will meet.</li>
  <li><a href="{REPO}/blob/main/docs/PRODUCTION-GAPS.md" target="_blank" rel="noopener">Production gaps</a>: what the free reference does not do, and what an enterprise replaces.</li>
  <li>On this site: <a href="/academy/modules/2026/FSE/spring-ecosystem-and-spring-ai.html">the Spring ecosystem and Spring AI</a>, <a href="/academy/modules/2026/FSE/java-evolution-8-to-27.html">Java release by release</a>, and <a href="/academy/modules/2026/FSE/mcp-end-to-end.html">MCP end to end</a>.</li>
</ul>
<div class="cta" style="margin-top:22px">
  <div>
    <h3>Cook it yourself.</h3>
    <p>Clone the repository, run the four commands, log in as alice, and change the first decision you disagree with. The ADR tells you what breaks.</p>
  </div>
  <div class="actions" style="margin-top:0">
    <a class="btn primary" href="{REPO}" target="_blank" rel="noopener">Clone AssetCare ↗</a>
    <a class="btn" href="/academy/">Back to the Academy</a>
  </div>
</div>
      </div>
    </div>
  </section>
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
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w", encoding="utf-8").write(page)
print(f"wrote {os.path.relpath(OUT, ROOT)} ({len(page)//1024} KB, {page.count('<section')} sections)")
