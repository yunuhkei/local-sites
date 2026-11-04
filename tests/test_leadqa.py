import os, sys, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "leadfinder")); sys.path.insert(0, os.path.join(ROOT, "sitemaker"))
import leadqa, osm_hours  # noqa: E402


def row(i, name, typ="Barbershop", phone="", lat=43.17, lon=-87.99, **kw):
    return dict({"id": i, "name": name, "type": typ, "phone": phone, "lat": lat, "lon": lon, "hours": "", "updated": "", "email": "", "social": ""}, **kw)


class Clean(unittest.TestCase):
    def test_reasons(self):
        rows = [row("1", "Good Cuts"), row("2", "St. Mark Lutheran Church"), row("3", "Milwaukee Public Library"),
                row("4", "McDonald's"), row("5", "Old Place (closed)"), row("6", "Bright Kids Learning Center", "Daycare")]
        kept, removed = leadqa.clean(rows)
        self.assertEqual([r["id"] for r in kept], ["1", "6"])          # learning centers are real daycares: kept
        self.assertEqual(len(removed), 4)

    def test_duplicates_and_chains(self):
        rows = [row("1", "Tasty Spot", "Restaurant", "414-555-0101"), row("2", "Tasty Spot", "Restaurant", "(414) 555-0101"),
                row("3", "Chainy", "Restaurant", lat=43.2), row("4", "Chainy", "Restaurant", lat=43.3), row("5", "Chainy", "Restaurant", lat=43.4)]
        kept, removed = leadqa.clean(rows)
        self.assertEqual([r["id"] for r in kept], ["1"])
        self.assertEqual(sorted(reason for _, reason in removed).count("duplicate"), 1)

    def test_blocked_ids(self):
        kept, removed = leadqa.clean([row("1", "Good Cuts")], blocked_ids={"1"})
        self.assertEqual(kept, [])

    def test_score_order(self):
        near = row("1", "A", "Barbershop", "414-555-0101", hours="Mo-Fr 09:00-17:00", updated="2026-01-01")
        far = row("2", "B", "Car wash", "", lat=43.25, lon=-88.1)
        self.assertGreater(leadqa.score_parts(near)[0], leadqa.score_parts(far)[0])
        self.assertAlmostEqual(leadqa.miles(43.17, -87.99), 0.0, places=3)


class Hours(unittest.TestCase):
    def test_simple(self):
        h = osm_hours.parse("Mo-Fr 09:00-17:00; Sa 10:00-14:00; Su off")
        self.assertEqual(h[0], ["Monday", "09:00-17:00"])
        self.assertEqual(h[5], ["Saturday", "10:00-14:00"])
        self.assertEqual(h[6], ["Sunday", "Closed"])

    def test_unmentioned_day_closed_and_override(self):
        h = osm_hours.parse("Mo-Sa 10:00-18:00; We off")
        self.assertEqual(h[2][1], "Closed"); self.assertEqual(h[6][1], "Closed")

    def test_refuses_to_guess(self):
        for t in ("Mo-Fr 09:00-12:00,13:00-17:00", "Mo-Su 10:00-02:00", "24/7", "Mo-Fr sunrise-sunset", "PH off", "", None):
            self.assertIsNone(osm_hours.parse(t), t)


if __name__ == "__main__":
    unittest.main()
