#!/usr/bin/env python3
"""Find Milwaukee-area small businesses that have NO website listed in OpenStreetMap.

Free & legal source: the OpenStreetMap Overpass API (data (c) OpenStreetMap
contributors, ODbL license). No scraping of Google Maps or anything else.

Usage:
    python3 leadfinder/find_leads.py                  # search & update data/leads.csv
    python3 leadfinder/find_leads.py --radius 8000    # smaller search area (meters)
    python3 leadfinder/find_leads.py --from-file tests/fixtures/overpass_sample.json --csv /tmp/x.csv

Only the Python standard library is used, so there is nothing to install.
"""
import argparse
import csv
import datetime
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

# Default search center: roughly ZIP 53218 (north-west Milwaukee). Radius in meters.
DEFAULT_LAT = 43.1700
DEFAULT_LON = -87.9900
DEFAULT_RADIUS = 12000

# Public Overpass servers; we try them in order.
OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]
USER_AGENT = "local-sites-lead-finder/1.0 (personal side project, Milwaukee WI)"

STATUSES = ["new", "contacted", "interested", "paid", "not interested"]
FIELDS = ["id", "name", "type", "address", "phone", "social", "status",
          "found_date", "lat", "lon", "notes"]

# OSM tag keys that mean "this business already has a website".
WEBSITE_KEYS = ("website", "contact:website", "url", "contact:url")

# Which OSM tags we look for. key -> {value: human label}
SHOP_LABELS = {
    "barber": "Barbershop",
    "hairdresser": "Hair salon",
    "beauty": "Beauty salon",       # nails handled specially below
    "massage": "Massage",
    "tattoo": "Tattoo studio",
    "bakery": "Bakery",
    "butcher": "Butcher / meat market",
    "deli": "Deli",
    "dry_cleaning": "Dry cleaner",
    "laundry": "Laundry / cleaner",
    "car_repair": "Auto repair",
    "car_wash": "Car wash",
    "tyres": "Tire shop",
    "florist": "Florist",
    "pet_grooming": "Pet grooming",
    "locksmith": "Locksmith",
}
AMENITY_LABELS = {
    "restaurant": "Restaurant",
    "fast_food": "Fast food / takeout",
    "cafe": "Cafe",
    "food_truck": "Food truck",
    "car_wash": "Car wash",
    "childcare": "Daycare",
}
CRAFT_LABELS = {
    "plumber": "Plumber",
    "electrician": "Electrician",
    "hvac": "HVAC",
    "carpenter": "Carpenter",
    "painter": "Painter",
    "roofer": "Roofer",
    "gardener": "Landscaping",
}


def build_query(lat, lon, radius):
    """Overpass QL: named places with the tags above and NO website-ish tags."""
    no_site = "".join('[!"%s"]' % k for k in WEBSITE_KEYS)
    around = "(around:%d,%s,%s)" % (radius, lat, lon)

    def clause(key, labels):
        values = "|".join(sorted(labels))
        return 'nwr["%s"~"^(%s)$"]["name"]%s%s;' % (key, values, no_site, around)

    return (
        "[out:json][timeout:120];\n(\n  "
        + "\n  ".join([clause("shop", SHOP_LABELS),
                       clause("amenity", AMENITY_LABELS),
                       clause("craft", CRAFT_LABELS)])
        + "\n);\nout center tags;\n"
    )


def fetch_overpass(query, retries_per_server=2):
    """POST the query to the Overpass servers until one answers."""
    body = urllib.parse.urlencode({"data": query}).encode()
    last_err = None
    for url in OVERPASS_URLS:
        for attempt in range(retries_per_server):
            try:
                req = urllib.request.Request(url, data=body, headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(req, timeout=150) as resp:
                    return json.load(resp)
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as err:
                last_err = err
                print("  (server %s failed: %s)" % (url, err), file=sys.stderr)
                time.sleep(3 * (attempt + 1))
    raise SystemExit("Could not reach any Overpass server. Last error: %s" % last_err)


def label_for(tags):
    """Human-readable business type, or None if we don't serve this type."""
    shop, amenity, craft = tags.get("shop"), tags.get("amenity"), tags.get("craft")
    if shop == "hairdresser" and tags.get("hairdresser") == "barber":
        return "Barbershop"
    if shop == "beauty":
        beauty = tags.get("beauty", "")
        if "nails" in beauty:
            return "Nail salon"
        return SHOP_LABELS["beauty"]
    if amenity == "fast_food" and tags.get("fast_food") == "food_truck":
        return "Food truck"
    if shop in SHOP_LABELS:
        return SHOP_LABELS[shop]
    if amenity in AMENITY_LABELS:
        return AMENITY_LABELS[amenity]
    if craft in CRAFT_LABELS:
        return CRAFT_LABELS[craft]
    return None


def clean_phone(raw):
    """Format US numbers like (414) 555-0123; leave anything odd as-is."""
    if not raw:
        return ""
    first = re.split(r"[;,/]", raw)[0].strip()
    digits = re.sub(r"\D", "", first)
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) == 10:
        return "(%s) %s-%s" % (digits[:3], digits[3:6], digits[6:])
    return first


def make_address(tags):
    street = " ".join(p for p in (tags.get("addr:housenumber"), tags.get("addr:street")) if p)
    city = tags.get("addr:city", "")
    state = tags.get("addr:state", "")
    postcode = tags.get("addr:postcode", "")
    tail = " ".join(p for p in (state, postcode) if p)
    return ", ".join(p for p in (street, city, tail) if p)


SOCIAL_BASES = {"facebook": "https://facebook.com/", "instagram": "https://instagram.com/",
                "twitter": "https://twitter.com/", "tiktok": "https://tiktok.com/@",
                "youtube": "https://youtube.com/"}


def social_links(tags):
    """Collect social pages as full links (OSM sometimes stores just the handle)."""
    links = []
    for site, base in SOCIAL_BASES.items():
        for key in ("contact:" + site, site):
            val = (tags.get(key) or "").strip()
            if not val:
                continue
            if not val.startswith("http"):
                val = base + val.lstrip("@/")
            if val not in links:
                links.append(val)
    return " | ".join(links)


def parse_elements(data):
    """Turn an Overpass JSON response into a list of lead dicts (filters applied)."""
    leads = []
    for el in data.get("elements", []):
        tags = el.get("tags") or {}
        name = (tags.get("name") or "").strip()
        if not name:
            continue
        if any(tags.get(k) for k in WEBSITE_KEYS):
            continue                                  # already has a website
        if tags.get("brand") or tags.get("brand:wikidata"):
            continue                                  # chains / franchises are not our customers
        type_label = label_for(tags)
        if not type_label:
            continue
        phone = clean_phone(tags.get("phone") or tags.get("contact:phone") or tags.get("contact:mobile") or "")
        address = make_address(tags)
        if not (phone or tags.get("addr:street")):
            continue                                  # no way to find or reach them
        lat = el.get("lat") or (el.get("center") or {}).get("lat", "")
        lon = el.get("lon") or (el.get("center") or {}).get("lon", "")
        leads.append({
            "id": "osm-%s-%s" % (el.get("type", "node"), el.get("id")),
            "name": name,
            "type": type_label,
            "address": address,
            "phone": phone,
            "social": social_links(tags),
            "status": "new",
            "found_date": "",
            "lat": lat,
            "lon": lon,
            "notes": "",
        })
    return leads


def load_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_csv(path, rows):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def merge(existing, found, today):
    """Add only brand-new leads. Existing rows (and your statuses/notes) are never touched."""
    known = {r["id"] for r in existing}
    added = []
    for lead in found:
        if lead["id"] not in known:
            lead = dict(lead, found_date=today)
            added.append(lead)
            known.add(lead["id"])
    return existing + added, added


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", default="data/leads.csv", help="spreadsheet to update (default data/leads.csv)")
    ap.add_argument("--lat", type=float, default=float(os.environ.get("SEARCH_LAT", DEFAULT_LAT)))
    ap.add_argument("--lon", type=float, default=float(os.environ.get("SEARCH_LON", DEFAULT_LON)))
    ap.add_argument("--radius", type=int, default=int(os.environ.get("SEARCH_RADIUS", DEFAULT_RADIUS)),
                    help="search radius in meters (default 12000, about 7.5 miles)")
    ap.add_argument("--from-file", help="use a saved Overpass JSON file instead of the internet (for testing)")
    ap.add_argument("--print-query", action="store_true", help="show the Overpass query and exit")
    args = ap.parse_args(argv)

    query = build_query(args.lat, args.lon, args.radius)
    if args.print_query:
        print(query)
        return 0

    if args.from_file:
        with open(args.from_file, encoding="utf-8") as f:
            data = json.load(f)
    else:
        print("Searching OpenStreetMap near %s, %s (radius %d m)..." % (args.lat, args.lon, args.radius))
        data = fetch_overpass(query)

    found = parse_elements(data)
    existing = load_csv(args.csv)
    rows, added = merge(existing, found, datetime.date.today().isoformat())
    save_csv(args.csv, rows)

    print("Matching businesses without a website: %d" % len(found))
    print("New this run: %d   (total in spreadsheet: %d)" % (len(added), len(rows)))
    for lead in added[:15]:
        print("  + %s  [%s]  %s" % (lead["name"], lead["type"], lead["phone"] or lead["address"]))

    # Let GitHub Actions pass the number on to the phone-alert step.
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as f:
            f.write("new_count=%d\n" % len(added))
    return 0


if __name__ == "__main__":
    sys.exit(main())
