#!/usr/bin/env python3
"""Write the generated Schema.org JSON-LD block into every indexable page.

Run from anywhere:  python3 scripts/gen-structured-data.py   (or scripts/build.py)

Each page in content/site.json gets exactly one block

    <script type="application/ld+json" data-generated="gen-structured-data">…</script>

placed before </head> and rewritten in place on later runs. Its @graph is derived
from content/profile.json, content/projects.json and the page's own <title>,
description and og:image, so the structured data can only say what the site
already says:

    every page        BreadcrumbList (Home > section > page)
    /                 WebSite, ProfilePage, Person (full), the products and projects
    /resume/          ProfilePage, Person (full)
    /products/        ItemList of the products (SoftwareApplication)
    a project's page  SoftwareSourceCode / SoftwareApplication for that project
    academy and lab   TechArticle, unless the page already declares its own
    resource pages    Article, TechArticle, BlogPosting or Course

Hand-written blocks (blog Articles, the AssetCare case study, the Course pages)
stay; they must reference the person as {"@id": "https://janaka.me/#me"}, which
scripts/validate-site.py enforces. Entity ids are stable and must not change:
    https://janaka.me/#me        the person
    https://janaka.me/#website   the site
    <page url>#<slug>            a product or project, on the page that presents it
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import site_lib  # noqa: E402

MARK = 'data-generated="gen-structured-data"'
BLOCK_RE = re.compile(
    r'[ \t]*<script type="application/ld\+json" ' + re.escape(MARK) + r'>.*?</script>\n?', re.S)
ARTICLE_TYPES = {"Article", "TechArticle", "BlogPosting", "Course", "NewsArticle", "LearningResource"}
WEBSITE_ID = "https://janaka.me/#website"


def person_ref(profile):
    return {"@type": "Person", "@id": profile["id"], "name": profile["name"], "url": profile["url"]}


def person_full(profile, projects):
    loc = profile["location"]
    return {
        "@type": "Person",
        "@id": profile["id"],
        "name": profile["name"],
        "url": profile["url"],
        "image": profile["image"],
        "jobTitle": profile["jobTitle"],
        "description": profile["description"],
        "address": {"@type": "PostalAddress", "addressLocality": loc["locality"], "addressCountry": loc["country"]},
        "email": "mailto:" + profile["contact"]["email"],
        "sameAs": profile["sameAs"],
        "knowsLanguage": [lang["code"] for lang in profile["languages"]],
        "knowsAbout": profile["knowsAbout"],
        "owns": [{"@id": project_id(p)} for p in projects],
    }


def project_id(p):
    page = p["page"]
    return page if "#" in page else page + "#" + p["slug"]


def project_node(p, profile):
    node = {
        "@type": "SoftwareSourceCode" if p.get("source") else "SoftwareApplication",
        "@id": project_id(p),
        "name": p["name"],
        "description": p["summary"],
        "url": p["url"],
        "author": {"@id": profile["id"]},
    }
    if p.get("source"):
        node["codeRepository"] = p["source"]
        node["programmingLanguage"] = p.get("programmingLanguages", [])
        node["runtimePlatform"] = p.get("stack", [])
        if p.get("license"):
            node["license"] = p["license"]
    else:
        node["applicationCategory"] = p["applicationCategory"]
        node["operatingSystem"] = "Web"
    return node


def breadcrumb(page, parsed, site):
    sections = {s["id"]: s for s in site["sections"]}
    crumbs = [("Home", "https://janaka.me/")]
    sec = sections.get(page.section)
    if sec and page.section != "hub":
        crumbs.append((sec["name"], "https://janaka.me" + sec["path"]))
    if page.path not in ("/", sec["path"] if sec else None):
        crumbs.append((site_lib.clean_title(parsed.title) or page.path, page.url))
    if len(crumbs) < 2:
        return None
    return {
        "@type": "BreadcrumbList",
        "@id": page.url + "#breadcrumb",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": name, "item": url}
            for i, (name, url) in enumerate(crumbs)
        ],
    }


def own_types(parsed):
    """@types declared by the page's hand-written (non-generated) blocks."""
    types = set()
    try:
        for node in site_lib.jsonld_nodes(parsed.jsonld):
            t = node.get("@type")
            types.update(t if isinstance(t, list) else [t])
    except ValueError:
        pass
    return types


def graph_for(page, html, parsed, site, profile, projects):
    graph = []
    handwritten = site_lib.parse(BLOCK_RE.sub("", html))
    if page.path == "/":
        graph.append({"@type": "WebSite", "@id": WEBSITE_ID, "url": "https://janaka.me/",
                      "name": site["name"], "inLanguage": site["language"],
                      "publisher": {"@id": profile["id"]}})
    if page.path in ("/", "/resume/"):
        graph.append({"@type": "ProfilePage", "@id": page.url + "#profilepage", "url": page.url,
                      "name": site_lib.clean_title(parsed.title), "isPartOf": {"@id": WEBSITE_ID},
                      "mainEntity": {"@id": profile["id"]}})
        graph.append(person_full(profile, projects))
    if page.path == "/":
        graph.extend(project_node(p, profile) for p in projects)
    if page.path == "/products/":
        products = [p for p in projects if p["kind"] == "product"]
        graph.append({
            "@type": "ItemList", "@id": page.url + "#catalogue",
            "name": "Products by Janaka Premathilaka available for acquisition or licensing",
            "url": page.url,
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "item": project_node(p, profile)}
                                for i, p in enumerate(products)],
        })
    if page.path not in ("/", "/products/"):
        for p in projects:
            if p["page"] == page.url:
                graph.append(project_node(p, profile))
    if (page.kind == "resource" and page.section in ("academy", "lab")
            and not (own_types(handwritten) & ARTICLE_TYPES)):
        node = {
            "@type": "TechArticle",
            "@id": page.url + "#article",
            "headline": site_lib.clean_title(parsed.title),
            "description": site_lib.truncate(parsed.description(), 300),
            "url": page.url,
            "mainEntityOfPage": page.url,
            "inLanguage": parsed.lang or site["language"],
            "datePublished": site_lib.added(page.rel),
            "author": person_ref(profile),
            "isPartOf": {"@type": "WebPage", "@id": "https://janaka.me/" + page.section + "/"},
        }
        if parsed.metas.get("og:image"):
            node["image"] = parsed.metas["og:image"]
        graph.append(node)
    crumbs = breadcrumb(page, parsed, site)
    if crumbs:
        graph.append(crumbs)
    return graph


def render_block(graph):
    body = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, indent=2)
    body = "\n".join("  " + line for line in body.splitlines())
    return f'  <script type="application/ld+json" {MARK}>\n{body}\n  </script>\n'


def apply(html, block):
    if BLOCK_RE.search(html):
        return BLOCK_RE.sub(lambda _m: block, html, count=1)
    idx = html.lower().find("</head>")
    if idx < 0:
        raise ValueError("no </head>")
    return html[:idx] + block + html[idx:]


def main():
    site = site_lib.load_content("site.json")
    profile = site_lib.load_content("profile.json")
    projects = site_lib.load_content("projects.json")["projects"]
    changed = 0
    for page in site_lib.pages(site):
        path = os.path.join(site_lib.ROOT, page.rel)
        with open(path, encoding="utf-8", newline="") as fh:
            raw = fh.read()
        html = raw.replace("\r\n", "\n")
        parsed = site_lib.parse(html)
        graph = graph_for(page, html, parsed, site, profile, projects)
        out = apply(html, render_block(graph))
        if out != html:
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(out)
            changed += 1
    print(f"structured data: {changed} pages updated")


if __name__ == "__main__":
    main()
