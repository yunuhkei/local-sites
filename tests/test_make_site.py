import copy, json, os, sys, tempfile, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "sitemaker"))
import checks, make_site  # noqa: E402

BARBER = json.load(open(os.path.join(ROOT, "sites", "corner-chair-barbershop", "site.json")))
AUTO = json.load(open(os.path.join(ROOT, "sites", "60th-street-auto-repair", "site.json")))
HOURS = [["Monday", "Closed"], ["Tuesday", "10:00-19:30"]]


class Render(unittest.TestCase):
    def test_demo_page(self):
        h = make_site.render(BARBER, base_url="https://x.test/s")
        self.assertIn('href="tel:+14145550142"', h)
        self.assertIn("noindex", h)
        self.assertIn("TO GET FROM OWNER", h)            # hours missing -> labeled, not invented
        self.assertIn('property="og:image" content="https://x.test/s/og.png"', h)
        self.assertEqual(checks.scan_page(h), [])
        self.assertNotIn("{{", h)

    def test_hours_json_ld_and_format(self):
        c = dict(BARBER, hours=HOURS)
        h = make_site.render(c, base_url="https://x.test/s")
        self.assertIn("10 am – 7:30 pm", h)
        self.assertIn('"dayOfWeek": "Tuesday"', h)
        self.assertIn('data-day="2"', h)
        self.assertNotIn("TO GET FROM OWNER", h)

    def test_escaping_and_unsafe_links(self):
        c = dict(BARBER, name="Joe's <b>X</b>", hero_lines=None, social=["javascript:alert(1)"])
        c["design"] = dict(c["design"], hero_lines=["Joe's", "<b>X</b>"])
        h = make_site.render(c)
        self.assertNotIn("<b>X</b>", h.split("</style>")[1].split('"description"')[0] if False else h.replace("&lt;b&gt;X&lt;/b&gt;", ""))
        self.assertNotIn("javascript:", h)

    def test_live_has_no_banner_and_is_indexable(self):
        h = make_site.render(dict(BARBER, hours=HOURS), live=True)
        self.assertNotIn("noindex", h)
        self.assertNotIn('class="banner"', h)
        self.assertIn("canonical", h)
        self.assertEqual(checks.scan_page(h, live=True), [])

    def test_live_with_todo_fails_scan(self):
        h = make_site.render(BARBER, live=True)
        self.assertTrue(any("TO GET FROM OWNER" in e for e in checks.scan_page(h, live=True)))


class Rules(unittest.TestCase):
    def test_contrast(self):
        self.assertAlmostEqual(checks.contrast("#000000", "#ffffff"), 21.0, places=1)
        bad = dict(BARBER["design"]["palette"], muted="#e0d8c8")
        self.assertTrue(any("muted" in e for e in checks.check_palette(bad)))
        self.assertEqual(checks.check_palette(BARBER["design"]["palette"]), [])

    def test_banned_copy_and_emoji(self):
        page = "<h1>x</h1><p>We love to elevate your look with passion \U0001F600</p>:focus-visible"
        errs = " ".join(checks.scan_page(page))
        self.assertIn("elevate", errs)
        self.assertIn("passion", errs)
        self.assertIn("emoji", errs)

    def test_banned_heading_font(self):
        c = copy.deepcopy(BARBER)
        c["design"]["fonts"]["head"] = "Poppins"
        self.assertTrue(any("heading font" in e for e in make_site.validate_config(c)))

    def test_design_log_rule(self):
        a = checks.design_entry(BARBER, BARBER["design"]["section_order"])
        b = checks.design_entry(AUTO, AUTO["design"]["section_order"])
        self.assertEqual(checks.design_conflicts(b, [a]), [])          # our two samples are different
        twin = dict(a, slug="twin", business="Twin")                     # an exact copy shares everything
        self.assertEqual(len(checks.design_conflicts(twin, [a])), 1)
        one_shared = dict(b, slug="x", layout=a["layout"])               # sharing only the layout is allowed
        self.assertEqual(checks.design_conflicts(one_shared, [a]), [])

    def test_brief_required(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertTrue(checks.check_brief(os.path.join(d, "brief.md")))   # missing
            open(os.path.join(d, "brief.md"), "w").write("# x\n## Customers\nhi\n")
            self.assertTrue(checks.check_brief(os.path.join(d, "brief.md")))   # incomplete
        for s in ("corner-chair-barbershop", "60th-street-auto-repair"):
            self.assertEqual(checks.check_brief(os.path.join(ROOT, "sites", s, "brief.md")), [])


class Build(unittest.TestCase):
    def test_build_refuses_without_brief_and_blocks_live(self):
        with tempfile.TemporaryDirectory() as d:
            sd = os.path.join(d, "sites", "x"); os.makedirs(sd)
            c = copy.deepcopy(BARBER); c["slug"] = "x"
            json.dump(c, open(os.path.join(sd, "site.json"), "w"))
            self.assertEqual(make_site.main([os.path.join(sd, "site.json"), "--out", d, "--log", os.path.join(d, "l.json"), "--skip-assets"]), 1)
            for f in ("brief.md",):
                open(os.path.join(sd, f), "w").write(open(os.path.join(ROOT, "sites", "corner-chair-barbershop", f)).read())
            args = [os.path.join(sd, "site.json"), "--out", d, "--log", os.path.join(d, "l.json"), "--skip-assets"]
            self.assertEqual(make_site.main(args + ["--live"]), 1)       # sample + missing hours -> blocked
            self.assertEqual(make_site.main(args), 0)
            self.assertTrue(os.path.exists(os.path.join(d, "x", "index.html")))
            self.assertTrue(os.path.exists(os.path.join(d, "x", "404.html")))


if __name__ == "__main__":
    unittest.main()
