import os, sys, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "sitemaker"))
import make_site  # noqa: E402


class MakeSiteTests(unittest.TestCase):
    cfg = {"name": 'Joe\'s <b>Cuts</b>', "type": "Barbershop", "phone": "(414) 555-0123",
           "address": "1 Main St, Milwaukee, WI 53218", "social": ["javascript:alert(1)", "https://facebook.com/joe"]}

    def test_demo(self):
        h = make_site.render(self.cfg)
        self.assertIn('href="tel:+14145550123"', h)
        self.assertIn("noindex", h)
        self.assertIn("not their official website yet", h)
        self.assertIn("google.com/maps/search", h)
        self.assertNotIn("<b>Cuts</b>", h)          # escaped
        self.assertNotIn("javascript:", h)           # unsafe link dropped
        self.assertIn("facebook.com/joe", h)
        self.assertNotIn("{{", h)

    def test_live(self):
        h = make_site.render(self.cfg, live=True)
        self.assertNotIn("noindex", h)
        self.assertNotIn("demo-bar", h.split("</style>")[1])
        self.assertNotIn("Your photo here", h)       # no placeholders on a live site
        self.assertIn("application/ld+json", h)

    def test_templates_and_defaults(self):
        for t, tpl in [("Nail salon", "salon"), ("Restaurant", "food"), ("Auto repair", "service")]:
            h = make_site.render({"name": "X", "type": t, "phone": "4145550000"})
            self.assertIn('class="%s is-demo"' % tpl, h)


if __name__ == "__main__":
    unittest.main()
