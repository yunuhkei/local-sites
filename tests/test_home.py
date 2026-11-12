import json, os, subprocess, sys, tempfile, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "sitemaker"))
import build_home, checks  # noqa: E402


class Home(unittest.TestCase):
    def cfg(self, **kw):
        c = json.load(open(os.path.join(ROOT, "config.json")))
        c.update(base="https://x.test", phone="", email="", formspree_id="", stripe_link="", custom_domain="")
        c.update(kw)
        return c

    def test_draft_has_labeled_todos_and_noindex(self):
        page = build_home.home(self.cfg(), live=False)
        self.assertIn("noindex", page)
        self.assertIn("TO GET FROM OWNER: phone number", page)
        self.assertEqual(checks.scan_page(page), [])

    def test_public_when_complete(self):
        c = self.cfg(phone="(414) 555-0100", email="a@example.com", formspree_id="abc", stripe_link="https://buy.stripe.com/x")
        page = build_home.home(c, live=True)
        self.assertNotIn("noindex", page)
        self.assertNotIn("TO GET FROM OWNER", page)
        self.assertIn('href="tel:+14145550100"', page)
        self.assertIn('action="https://formspree.io/f/abc"', page)
        self.assertIn('name="_gotcha"', page)                      # spam honeypot
        self.assertIn("ProfessionalService", page)
        self.assertEqual(checks.scan_page(page, live=True), [])

    def test_no_fake_proof_and_palette(self):
        page = build_home.home(self.cfg(), live=False).lower()
        for bad in ("testimonial", "reviews", "clients served", "award"):
            self.assertNotIn(bad, page)
        self.assertEqual(checks.check_palette(build_home.PALETTE), [])

    def test_prices_come_from_config(self):
        page = build_home.price_sheet(self.cfg())
        self.assertIn("$500", page); self.assertIn("$250", page); self.assertIn("$25", page)


if __name__ == "__main__":
    unittest.main()
