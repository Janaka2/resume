#!/usr/bin/env python3
"""Generate the machine-readable views of janaka.me: static JSON and llms.txt.

Run from anywhere:  python3 scripts/gen-public-data.py   (after gen-content-index.py;
scripts/build.py runs everything in order)

Writes
    api/public/v1/index.json             catalogue of everything below
    api/public/v1/profile.json           identity, experience, certifications, education
    api/public/v1/projects.json          products and reference projects
    api/public/v1/projects/<slug>.json   one project
    api/public/v1/resources.json         articles, academy and lab pages (from the content index)
    llms.txt                             short map of the site for language models
    llms-full.txt                        the same with profile, experience and every page summary

Inputs: content/*.json, assets/content-index.json, and the hub partials
experience.html, certifications.html and education.html, parsed so the JSON says
exactly what the visible CV says. The files are read-only static JSON (GitHub Pages
has no server); the WebMCP tools in assets/js/agent/ read them too. Shapes are
documented in docs/ai/discovery.md; change them only with an apiVersion bump.

Every output passes assert_public() before it is written: no phone numbers, no
credentials, no key material, nothing the site does not already publish.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import site_lib  # noqa: E402

API_VERSION = "1"
API_DIR = os.path.join("api", "public", "v1")
ORIGIN = "https://janaka.me"

PRIVATE_KEYS = re.compile(r"(pass(word)?|secret|token|api[_-]?key|phone|tel|whatsapp|credential)s?$", re.I)
PRIVATE_VALUES = [
    re.compile(r"\btel:"),
    re.compile(r"\+?\d{2}[\s-]?\d{2}[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}\b"),   # phone numbers
    re.compile(r"AssetCare-Demo-\d{4}"),                                     # demo password
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\b(sk|pk|ghp|gho|hf)_[A-Za-z0-9]{16,}"),
    re.compile(r"\bsk-[A-Za-z0-9-]{20,}"),
]


class PrivateDataError(ValueError):
    pass


def assert_public(obj, where="output"):
    """Raise PrivateDataError if obj (JSON value or text) carries anything private."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if PRIVATE_KEYS.search(str(k)):
                raise PrivateDataError(f"{where}: private key {k!r}")
            assert_public(v, f"{where}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            assert_public(v, f"{where}[{i}]")
    elif isinstance(obj, str):
        for pat in PRIVATE_VALUES:
            if pat.search(obj):
                raise PrivateDataError(f"{where}: value matches {pat.pattern!r}")


# --- extraction from the visible CV ------------------------------------------

def experience(html):
    tl = site_lib.dom(html).find("ul", "tl")
    roles = []
    for li in (tl.elements() if tl else []):
        if li.tag != "li":
            continue
        when, title, org = li.find("p", "when"), li.find("h3"), li.find("p", "org")
        period = when.find("b").text() if when and when.find("b") else ""
        place = when.text()[len(period):].strip(" ·") if when else ""
        points = li.find("ul", "points")
        roles.append({
            "period": period,
            "location": place,
            "title": title.text() if title else "",
            "organisation": org.text() if org else "",
            "highlights": [p.text() for p in (points.find_all("li") if points else [])],
            "technologies": [c.text() for c in li.find_all("span", "chip")],
        })
    return roles


def certifications(html):
    root = site_lib.dom(html)
    section = root.find("section") or root
    out, group = [], ""
    for el in section.find("div", "wrap").elements() if section.find("div", "wrap") else []:
        if el.tag == "p" and "zlabel" in el.classes:
            group = el.text()
        elif el.tag == "div" and "cards3" in el.classes:
            for card in el.find_all("div", "card"):
                subs = [p.text() for p in card.find_all("p", "sub")]
                links = [a.attrs.get("href", "") for a in card.find_all("a")]
                out.append({
                    "group": group,
                    "name": card.find("h3").text() if card.find("h3") else "",
                    "issuer": next((s.split(":", 1)[1].strip() for s in subs if ":" in s.split(" ")[0]), ""),
                    "status": [s for s in subs if ":" not in s.split(" ")[0] and "certificate" not in s.lower()],
                    "evidence": [l if l.startswith("http") else ORIGIN + l for l in links if l],
                })
    return out


def education(html):
    sec = site_lib.dom(html)
    out = []
    for card in sec.find_all("div", "card"):
        ps = card.find_all("p")
        out.append({
            "institution": card.find("h3").text() if card.find("h3") else "",
            "degree": ps[0].text() if ps else "",
            "period": ps[1].text() if len(ps) > 1 else "",
        })
    return out


# --- documents ---------------------------------------------------------------

def envelope(canonical, **data):
    return {"apiVersion": API_VERSION, "canonical": canonical, **data}


def build_profile(profile, partials):
    person = {k: v for k, v in profile.items() if not k.startswith("$")}
    return envelope(profile["url"], person=person,
                    experience=experience(partials["experience"]),
                    certifications=certifications(partials["certifications"]),
                    education=education(partials["education"]))


def project_doc(p):
    doc = {k: v for k, v in p.items() if not k.startswith("$")}
    doc["api"] = f"{ORIGIN}/api/public/v1/projects/{p['slug']}.json"
    return doc


def build_resources(index, sections):
    names = {s["id"]: s["name"] for s in sections}
    return envelope(ORIGIN + "/", resources=[{
        "url": ORIGIN + e["url"],
        "path": e["url"],
        "title": e["title"],
        "section": e["section"],
        "sectionName": names.get(e["section"], e["section"]),
        "description": e["description"],
        "tags": e["tags"],
        "published": e["date"],
        "updated": e["updated"],
        "readingMinutes": e["minutes"],
    } for e in index])


def build_catalogue(site, profile, projects):
    return envelope(ORIGIN + "/", name=site["name"], description=profile["positioning"],
                    person=profile["id"],
                    sections=[{**s, "url": ORIGIN + s["path"]} for s in site["sections"]],
                    endpoints={
                        "profile": f"{ORIGIN}/api/public/v1/profile.json",
                        "projects": f"{ORIGIN}/api/public/v1/projects.json",
                        "project": f"{ORIGIN}/api/public/v1/projects/{{slug}}.json",
                        "resources": f"{ORIGIN}/api/public/v1/resources.json",
                    },
                    projectSlugs=[p["slug"] for p in projects],
                    discovery={
                        "sitemap": f"{ORIGIN}/sitemap.xml",
                        "feed": f"{ORIGIN}/feed.xml",
                        "llms": f"{ORIGIN}/llms.txt",
                        "llmsFull": f"{ORIGIN}/llms-full.txt",
                    })


# --- llms.txt ----------------------------------------------------------------

def _link(title, url, note=""):
    return f"- [{title}]({url})" + (f": {note}" if note else "")


def render_llms(site, profile, projects, resources, full=False):
    by_section = {}
    for r in resources:
        by_section.setdefault(r["section"], []).append(r)
    L = [f"# {profile['name']}", "", f"> {profile['jobTitle']}, {profile['location']['locality']}, Switzerland. "
         f"{profile['positioning']}", "",
         "Every page linked here is plain HTML that reads without JavaScript. "
         "The same facts are available as JSON under /api/public/v1/ and as Schema.org JSON-LD in each page.", ""]

    L += ["## Profile", ""]
    L.append(_link("Home", ORIGIN + "/", profile["description"]))
    L.append(_link("CV", profile["cv"]["page"], "experience, certifications, education and stack, English and German"))
    L.append(_link("Profile JSON", f"{ORIGIN}/api/public/v1/profile.json", "the CV as structured data"))
    L.append(_link("Contact", profile["contact"]["page"], "email " + profile["contact"]["email"]))
    L.append("")

    if full:
        pdata = build_profile(profile, _partials())
        L += ["### Experience", ""]
        for r in pdata["experience"]:
            L.append(f"- {r['period']} · {r['title']}, {r['organisation']} ({r['location']})")
            L += [f"  - {h}" for h in r["highlights"]]
        L += ["", "### Certifications and courses", ""]
        for c in pdata["certifications"]:
            status = "; ".join(c["status"])
            L.append(f"- {c['name']} ({c['issuer']})" + (f": {status}" if status else ""))
        L += ["", "### Education", ""]
        L += [f"- {e['institution']}: {e['degree']}, {e['period']}" for e in pdata["education"]]
        L += ["", "### Languages", ""]
        L += [f"- {lang['name']}: {lang['level']}" for lang in profile["languages"]]
        L.append("")

    L += ["## Projects and products", ""]
    for p in projects:
        L.append(_link(p["name"], p["page"], p["summary"] + (" " + p["availability"] if full else "")))
        if full:
            L.append(f"  - Live: {p['url']}" + (f" · Source: {p['source']}" if p.get("source") else ""))
            if p.get("stack"):
                L.append("  - Stack: " + ", ".join(p["stack"]))
            L += [f"  - {n}" for n in p.get("notes", [])]
    L.append("")

    sections = {s["id"]: s for s in site["sections"]}
    for sid in ("blog", "ai", "lab", "academy", "products"):
        items = by_section.get(sid, [])
        if not full and sid == "academy":
            # the learning paths and handbooks, not every study page
            items = [r for r in items if r["path"].endswith("/") or r["path"].endswith("Edition.html")]
        if not full and sid == "products":
            continue
        sec = sections[sid]
        L += [f"## {sec['name']}", "", _link(sec["name"], ORIGIN + sec["path"], sec["summary"])]
        L += [_link(r["title"], r["url"], r["description"]) for r in items if r["path"] != sec["path"]]
        L.append("")

    L += ["## Optional", ""]
    L.append(_link("Full version of this file", f"{ORIGIN}/llms-full.txt", "profile, experience and every page summary"))
    L.append(_link("Public JSON catalogue", f"{ORIGIN}/api/public/v1/index.json"))
    L.append(_link("Atom feed", f"{ORIGIN}/feed.xml"))
    L.append(_link("Sitemap", f"{ORIGIN}/sitemap.xml"))
    return "\n".join(L).rstrip() + "\n"


def _partials(root=site_lib.ROOT):
    return {n: site_lib.read(f"partials/{n}.html", root) for n in ("experience", "certifications", "education")}


# --- main --------------------------------------------------------------------

def build(root=site_lib.ROOT):
    """Return {repo-relative path: text} for every output. Pure apart from reads."""
    site = site_lib.load_content("site.json")
    profile = site_lib.load_content("profile.json")
    projects = site_lib.load_content("projects.json")["projects"]
    with open(os.path.join(root, "assets", "content-index.json"), encoding="utf-8") as fh:
        index = json.load(fh)

    resources = build_resources(index, site["sections"])
    docs = {
        "index.json": build_catalogue(site, profile, projects),
        "profile.json": build_profile(profile, _partials(root)),
        "projects.json": envelope(ORIGIN + "/products/", projects=[project_doc(p) for p in projects]),
        "resources.json": resources,
    }
    for p in projects:
        docs[f"projects/{p['slug']}.json"] = envelope(p["page"], project=project_doc(p))

    out = {}
    for name, doc in docs.items():
        assert_public(doc, name)
        out[os.path.join(API_DIR, name).replace(os.sep, "/")] = json.dumps(doc, ensure_ascii=False, indent=1) + "\n"
    for name, full in (("llms.txt", False), ("llms-full.txt", True)):
        text = render_llms(site, profile, projects, resources["resources"], full=full)
        assert_public(text, name)
        out[name] = text
    return out


def main():
    outputs = build()
    changed = sum(site_lib.write_if_changed(os.path.join(site_lib.ROOT, rel), text) for rel, text in outputs.items())
    # drop per-project files for projects that no longer exist
    pdir = os.path.join(site_lib.ROOT, API_DIR, "projects")
    for fn in os.listdir(pdir):
        if f"{API_DIR}/projects/{fn}".replace(os.sep, "/") not in outputs:
            os.remove(os.path.join(pdir, fn))
            changed += 1
    print(f"public data: {len(outputs)} files, {changed} changed")


if __name__ == "__main__":
    main()
