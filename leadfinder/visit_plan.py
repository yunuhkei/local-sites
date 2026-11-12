#!/usr/bin/env python3
"""Write data/visit-plan.md: two short driving routes with a Google Maps link, best times,
demo links and talking points for the Top 10. Talking points live in data/talking_points.json."""
import csv, json, math, os, sys, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, "sitemaker"))
import leadqa, make_site  # noqa: E402

def load():
    plan = json.load(open(os.path.join(ROOT, "data", "visit_plan.json"), encoding="utf-8"))
    conf = json.load(open(os.path.join(ROOT, "config.json"), encoding="utf-8"))
    rows = {r["name"]: r for r in csv.DictReader(open(os.path.join(ROOT, "data", "leads.csv"), encoding="utf-8"))}
    return plan, conf, rows

def maps_route(stops):
    pts = ["%s,%s" % (s["lat"], s["lon"]) for s in stops]
    return "https://www.google.com/maps/dir/?api=1&travelmode=driving&destination=%s&waypoints=%s" % (
        pts[-1], urllib.parse.quote("|".join(pts[:-1]), safe=",|"))

def leg_miles(a, b):
    return (leadqa.miles(a["lat"], a["lon"], (float(b["lat"]), float(b["lon"]))) or 0) * 1.3

def main():
    plan, conf, rows = load()
    base = conf["pages_base"].rstrip("/")
    out = ["# Visit plan\n",
           "Two short routes, each about 1.5-2 hours with 5 stops. **Before each stop: tap the Google check link, mark the lead *contacted* afterward, and read `pitch/walk-in-script.md`.** "
           "Demo links go live when the pull request is merged and Pages is on. Phone numbers come from OpenStreetMap; where directories disagree it says so.\n"]
    for route in plan["routes"]:
        stops = []
        for st in route["stops"]:
            r = rows[st["name"]]
            stops.append(dict(st, lead=r, lat=r["lat"], lon=r["lon"], slug=make_site.lead_slug(r)))
        miles = sum(leg_miles(stops[i], stops[i + 1]) for i in range(len(stops) - 1))
        out.append("\n## %s\n" % route["title"])
        out.append("**When:** %s  \n**Distance between stops:** about %.1f miles (%d stops), start wherever you are  \n**Google Maps route:** [Open the route](%s)\n" % (route["when"], miles, len(stops), maps_route(stops)))
        for i, s in enumerate(stops, 1):
            r = s["lead"]
            q = urllib.parse.quote("%s %s" % (r["name"], r["address"]))
            out.append("\n### %d. %s\n" % (i, r["name"]))
            out.append("- **Address:** %s ([map](https://www.google.com/maps/search/?api=1&query=%s))" % (r["address"], q))
            out.append("- **Phone:** %s%s" % (r["phone"], "  (%s)" % s["phone_note"] if s.get("phone_note") else ""))
            out.append("- **Best time:** %s" % s["best_time"])
            out.append("- **Demo:** %s/%s/  (preview, labeled not official)" % (base, s["slug"]))
            out.append("- **Check first:** [Google](https://www.google.com/search?q=%s)" % urllib.parse.quote(r["name"] + " Milwaukee"))
            out.append("- **Say:**")
            for t in s["points"]:
                out.append("  - %s" % t)
            out.append("- **At the visit, get:** a photo of the sign (for their colors), their hours, a photo of the shop, how they describe themselves (see `pitch/owner-intake.md`)")
    open(os.path.join(ROOT, "data", "visit-plan.md"), "w", encoding="utf-8").write("\n".join(out) + "\n")
    print("\n".join(out))

if __name__ == "__main__":
    main()
