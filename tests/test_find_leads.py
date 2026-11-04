import csv
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "leadfinder"))
import find_leads  # noqa: E402

FIXTURE = os.path.join(ROOT, "tests", "fixtures", "overpass_sample.json")


class FindLeadsTests(unittest.TestCase):
    def setUp(self):
        with open(FIXTURE, encoding="utf-8") as f:
            self.data = json.load(f)

    def test_filters(self):
        leads = find_leads.parse_elements(self.data)
        names = {l["name"] for l in leads}
        self.assertEqual(names, {"Test Barbershop", "Test Nails", "Test Taco Truck",
                                 "Test Little Learners Daycare"})
        # excluded: has website, chain, no contact info, no name, has contact:website

    def test_fields(self):
        by_name = {l["name"]: l for l in find_leads.parse_elements(self.data)}
        b = by_name["Test Barbershop"]
        self.assertEqual(b["type"], "Barbershop")
        self.assertEqual(b["phone"], "(414) 555-0101")
        self.assertEqual(b["address"], "100 W Example Ave, Milwaukee, WI 53218")
        self.assertIn("facebook.com/test-barbershop", b["social"])
        self.assertEqual(b["status"], "new")
        self.assertEqual(by_name["Test Nails"]["type"], "Nail salon")
        self.assertEqual(by_name["Test Nails"]["phone"], "(414) 555-0102")
        self.assertEqual(by_name["Test Nails"]["lat"], 43.18)          # way uses "center"
        self.assertEqual(by_name["Test Taco Truck"]["type"], "Food truck")
        self.assertEqual(by_name["Test Little Learners Daycare"]["type"], "Daycare")

    def test_merge_keeps_status_and_dedupes(self):
        found = find_leads.parse_elements(self.data)
        rows, added = find_leads.merge([], found, "2026-01-01")
        self.assertEqual(len(added), 4)
        rows[0]["status"] = "interested"
        rows[0]["notes"] = "call back Tue"
        rows2, added2 = find_leads.merge(rows, found, "2026-01-08")
        self.assertEqual(added2, [])
        self.assertEqual(rows2[0]["status"], "interested")
        self.assertEqual(rows2[0]["notes"], "call back Tue")
        self.assertEqual(rows2[0]["found_date"], "2026-01-01")

    def test_cli_end_to_end(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "leads.csv")
            self.assertEqual(find_leads.main(["--from-file", FIXTURE, "--csv", path]), 0)
            self.assertEqual(find_leads.main(["--from-file", FIXTURE, "--csv", path]), 0)  # 2nd run: no dupes
            with open(path, newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), 4)
            self.assertEqual(list(rows[0].keys()), find_leads.FIELDS)

    def test_query_shape(self):
        q = find_leads.build_query(43.17, -87.99, 5000)
        self.assertIn('[!"website"]', q)
        self.assertIn("around:5000,43.17,-87.99", q)
        self.assertTrue(q.rstrip().endswith("out center tags;"))


if __name__ == "__main__":
    unittest.main()
