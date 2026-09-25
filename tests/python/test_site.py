"""Tests for the janaka.me generators and validator. Stdlib only.

Run: python3 -m unittest discover -s tests/python
"""
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from xml.dom import minidom

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS = os.path.join(ROOT, "scripts")
sys.path.insert(0, SCRIPTS)
import site_lib  # noqa: E402


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, os.path.join(SCRIPTS, file))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sd = load("gen_structured_data", "gen-structured-data.py")
pub = load("gen_public_data", "gen-public-data.py")
sm = load("gen_sitemap", "gen-sitemap.py")
val = load("validate_site", "validate-site.py")
scan = load("maintenance_scan", "maintenance-scan.py")

FIXTURE = {
    "slug": "fixture-app", "name": "Fixture App", "kind": "product",
    "summary": "A test product that only exists in this test.",
    "url": "https://fixture.example/", "page": "https://janaka.me/products/#fixture-app",
    "status": "live", "availability": "Open to acquisition or licensing.",
    "applicationCategory": "UtilitiesApplication",
}


class Urls(unittest.TestCase):
    def test_site_path(self):
        self.assertEqual(site_lib.site_path("index.html"), "/")
        self.assertEqual(site_lib.site_path("ai/index.html"), "/ai/")
        self.assertEqual(site_lib.site_path("lab/Notes/llm-hand‑annotated-demo5.html"),
                         "/lab/Notes/llm-hand%E2%80%91annotated-demo5.html")

    def test_file_for_path_round_trip(self):
        for rel in ("index.html", "ai/index.html", "lab/Notes/llm-hand‑annotated-demo5.html"):
            self.assertEqual(site_lib.file_for_path(site_lib.site_path(rel)), rel)
        self.assertIsNone(site_lib.file_for_path("https://evil.example/"))

    def test_validator_resolves_relative_links(self):
        self.assertEqual(val.resolve("blog/posts/a.html", "../index.html"), "blog/index.html")
        self.assertEqual(val.resolve("blog/posts/a.html", "/lab/"), "lab/index.html")
        self.assertEqual(val.resolve("index.html", "partials/x.html#y"), "partials/x.html")
        self.assertIsNone(val.resolve("index.html", "mailto:x@y.z"))
        self.assertIsNone(val.resolve("index.html", "#top"))
        self.assertTrue(val.resolve("index.html", "../../outside.html").startswith(".."))


class Inventory(unittest.TestCase):
    def test_pages_skip_aliases_stubs_scaffolds_and_excludes(self):
        with tempfile.TemporaryDirectory() as root:
            def put(rel, text):
                os.makedirs(os.path.dirname(os.path.join(root, rel)) or root, exist_ok=True)
                with open(os.path.join(root, rel), "w", encoding="utf-8") as fh:
                    fh.write(text)
            body = "<html><body>" + "x" * 2000 + "</body></html>"
            put("index.html", body)
            put("docs/a.html", body)
            put("docs/dup.html", body)
            put("docs/stub.html", "tiny")
            put("docs/draft.html", body.replace("x", "Add today's learning notes here", 1))
            put("docs/old/b.html", body)
            put("docs/notes-index.html", body)
            site = {
                "pages": [{"path": "index.html", "section": "hub", "kind": "landing"}],
                "crawl": [{"dir": "docs", "section": "academy", "recursive": True}],
                "landingPatterns": ["(^|/)notes-index\\.html$"],
                "exclude": ["^docs/old/"],
                "aliases": {"docs/dup.html": "docs/a.html"},
            }
            got = {pg.rel: (pg.kind, reason) for pg, reason in site_lib.pages(site, root, include_skipped=True)}
            live = [pg.rel for pg in site_lib.pages(site, root)]
        self.assertEqual(live, ["index.html", "docs/a.html", "docs/notes-index.html"])
        self.assertEqual(got["docs/notes-index.html"][0], "landing")
        self.assertTrue(got["docs/dup.html"][1].startswith("alias"))
        self.assertEqual(got["docs/stub.html"][1], "stub")
        self.assertEqual(got["docs/draft.html"][1], "scaffold/noindex")
        self.assertEqual(got["docs/old/b.html"][1], "excluded")

    def test_real_inventory_has_no_duplicate_urls(self):
        urls = [pg.url for pg in site_lib.pages()]
        self.assertEqual(len(urls), len(set(urls)))
        self.assertIn("https://janaka.me/", urls)
        aliases = site_lib.load_content("site.json")["aliases"]
        for alias in aliases:
            self.assertNotIn(site_lib.abs_url(alias), urls)


class Propagation(unittest.TestCase):
    """A new project added once to content/projects.json reaches every derived surface."""

    def setUp(self):
        self.site = site_lib.load_content("site.json")
        self.profile = site_lib.load_content("profile.json")
        self.projects = site_lib.load_content("projects.json")["projects"] + [FIXTURE]

    def graph(self, rel):
        page = next(pg for pg in site_lib.pages(self.site) if pg.rel == rel)
        html = site_lib.read(rel)
        return sd.graph_for(page, html, site_lib.parse(html), self.site, self.profile, self.projects)

    def test_hub_json_ld(self):
        g = self.graph("index.html")
        person = next(n for n in g if n.get("@type") == "Person")
        self.assertIn({"@id": "https://janaka.me/products/#fixture-app"}, person["owns"])
        self.assertTrue(any(n.get("name") == "Fixture App" for n in g))

    def test_products_item_list(self):
        g = self.graph("products/index.html")
        items = next(n for n in g if n.get("@type") == "ItemList")["itemListElement"]
        self.assertEqual(items[-1]["item"]["name"], "Fixture App")
        self.assertEqual(items[-1]["item"]["author"], {"@id": self.profile["id"]})

    def test_public_json_and_llms(self):
        doc = pub.project_doc(FIXTURE)
        self.assertEqual(doc["api"], "https://janaka.me/api/public/v1/projects/fixture-app.json")
        text = pub.render_llms(self.site, self.profile, self.projects, [], full=False)
        self.assertIn("[Fixture App](https://janaka.me/products/#fixture-app)", text)
        full = pub.render_llms(self.site, self.profile, self.projects, [], full=True)
        self.assertIn("Live: https://fixture.example/", full)

    def test_generated_block_is_idempotent(self):
        html = "<html><head><title>t</title></head><body></body></html>"
        block = sd.render_block([{"@type": "Thing", "name": "x"}])
        once = sd.apply(html, block)
        self.assertEqual(sd.apply(once, block), once)
        self.assertEqual(once.count('data-generated="gen-structured-data"'), 1)
        self.assertLess(once.index("gen-structured-data"), once.index("</head>"))
        json.loads(site_lib.parse(once).jsonld[0])


class PublicData(unittest.TestCase):
    def test_private_values_are_rejected(self):
        for bad in ({"phone": "x"}, {"password": "x"}, {"note": "call tel:+41000"},
                    {"n": "+41 76 224 84 45"}, {"n": "login AssetCare-Demo-2026"},
                    {"k": "sk-abcdefghijklmnopqrstuvwxyz"}, ["-----BEGIN RSA PRIVATE KEY-----"]):
            with self.assertRaises(pub.PrivateDataError, msg=bad):
                pub.assert_public(bad)
        pub.assert_public({"email": "janaka2@gmail.com", "years": "1999 — 2004", "stack": ["Java 25"]})

    def test_experience_is_read_from_the_visible_cv(self):
        html = """<section><ul class="tl"><li><p class="when"><b>01.2024 — present</b> · Zürich</p>
        <h3>Lead</h3><p class="org">UBS</p><ul class="points"><li>Did a thing.</li></ul>
        <div class="chips"><span class="chip">Java</span></div></li></ul></section>"""
        roles = pub.experience(html)
        self.assertEqual(roles, [{"period": "01.2024 — present", "location": "Zürich", "title": "Lead",
                                  "organisation": "UBS", "highlights": ["Did a thing."], "technologies": ["Java"]}])

    def test_real_outputs_are_public(self):
        for rel, text in pub.build().items():
            pub.assert_public(text if rel.endswith(".txt") else json.loads(text), rel)

    def test_profile_matches_hub(self):
        doc = pub.build_profile(site_lib.load_content("profile.json"), pub._partials())
        self.assertGreaterEqual(len(doc["experience"]), 4)
        self.assertTrue(all(r["title"] and r["organisation"] and r["period"] for r in doc["experience"]))
        self.assertTrue(any("Kubernetes" in c["name"] for c in doc["certifications"]))
        self.assertNotIn("phone", json.dumps(doc).lower())


class Sitemap(unittest.TestCase):
    def test_render_is_valid_xml_and_escaped(self):
        xml = sm.render([("https://janaka.me/a?b=1&c=2", "2026-09-25")])
        doc = minidom.parseString(xml)
        self.assertEqual(doc.getElementsByTagName("loc")[0].firstChild.nodeValue, "https://janaka.me/a?b=1&c=2")


class MaintenanceScan(unittest.TestCase):
    """The obsolescence radar: fixed dates, recurring checks, never-checked items, past years."""

    ITEMS = [
        {"id": "fixed", "topic": "t", "action": "a", "review_by": "2026-11-01", "checked": "2026-09-25"},
        {"id": "recurring", "topic": "t", "action": "a", "every_days": 30, "checked": "2026-09-01"},
        {"id": "never", "topic": "t", "action": "a", "every_days": 30, "checked": None},
        {"id": "fresh", "topic": "t", "action": "a", "every_days": 365, "checked": "2026-09-01"},
    ]

    def statuses(self, day):
        import datetime
        return {w["id"]: w["status"] for w in scan.watchlist(datetime.date.fromisoformat(day), self.ITEMS)}

    def test_watchlist_states(self):
        self.assertEqual(self.statuses("2026-09-02"), {"never": "never-checked"})
        self.assertEqual(self.statuses("2026-09-25")["recurring"], "due-soon")
        later = self.statuses("2026-11-02")
        self.assertEqual(later["fixed"], "overdue")
        self.assertEqual(later["recurring"], "overdue")
        self.assertNotIn("fresh", later)

    def test_real_watchlist_is_valid_and_ordered(self):
        import datetime
        out = scan.watchlist(datetime.date(2030, 1, 1))
        self.assertTrue(out)
        self.assertEqual(out[0]["status"], "overdue")
        report = val.Report()
        val.check_watchlist(report, {})
        self.assertEqual(report.results["watchlist"]["fail"], [])

    def test_past_year_titles_are_flagged(self):
        import datetime
        pages = [pg for pg in site_lib.pages() if "Edition" in pg.rel]
        self.assertEqual(scan.stale_years(datetime.date(2026, 9, 25), pages), [])
        flagged = scan.stale_years(datetime.date(2027, 1, 1), pages)
        self.assertTrue(flagged and flagged[0]["years"] == [2026])

    def test_scan_never_writes(self):
        import contextlib
        import io
        before = subprocess_status()
        with contextlib.redirect_stdout(io.StringIO()):
            scan.main(["--json"])
        self.assertEqual(subprocess_status(), before)


def subprocess_status():
    import subprocess
    return subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True).stdout


if __name__ == "__main__":
    unittest.main()
