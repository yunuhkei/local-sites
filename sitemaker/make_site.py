#!/usr/bin/env python3
"""Build one business website from a design brief + site.json.

    # 1) after you find a lead: make the starter files (does NOT build a site)
    python3 sitemaker/make_site.py --scaffold osm-node-123456
    # 2) write sites/<slug>/brief.md and fill in sites/<slug>/site.json (Claude can do this for you)
    # 3) build (checks every design rule; refuses if one is broken)
    python3 sitemaker/make_site.py sites/<slug>/site.json
    # 4) only after the owner says YES: go live / standalone folder for their own domain
    python3 sitemaker/make_site.py sites/<slug>/site.json --live --export out/<slug> --cname www.theirsite.com

Standard library only (Pillow is used for photos if installed; Node+Playwright make the
share-preview image). Nothing here needs a secret.
"""
import argparse
import csv
import datetime
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import checks  # noqa: E402

SCHEMA_TYPES = {
    "Barbershop": "HairSalon", "Hair salon": "HairSalon", "Nail salon": "NailSalon",
    "Beauty salon": "BeautySalon", "Restaurant": "Restaurant", "Fast food / takeout": "FastFoodRestaurant",
    "Cafe": "CafeOrCoffeeShop", "Food truck": "FoodEstablishment", "Bakery": "Bakery",
    "Auto repair": "AutoRepair", "Car wash": "AutoWash", "Dry cleaner": "DryCleaningOrLaundry",
    "Laundry / cleaner": "DryCleaningOrLaundry", "Daycare": "ChildCare", "Locksmith": "Locksmith",
    "Plumber": "Plumber", "Electrician": "Electrician", "Roofer": "RoofingContractor", "HVAC": "HVACBusiness",
}
SHOT_LISTS = {
    "Barbershop": ["Storefront straight-on, daytime, sign readable", "The chairs and mirrors, wide shot",
                   "A finished fade/cut (with the client's OK), from behind", "Barber at work, hands and clippers",
                   "The shop's sign or any hand-painted details up close"],
    "Auto repair": ["Storefront or bay doors with the sign readable", "Inside the shop, a car on the lift",
                    "The mechanic(s) at work (with their OK)", "Tools/wall of tires, a close detail",
                    "The waiting area"],
    "_default": ["Storefront straight-on in daylight, sign readable", "Inside, a wide shot of the main space",
                 "The owner or team at work (with their OK)", "Their best product/work, close up",
                 "Any hand-painted sign or detail that is uniquely theirs"],
}
DAY_INDEX = {"sun": 0, "mon": 1, "tue": 2, "wed": 3, "thu": 4, "fri": 5, "sat": 6}
SCHEMA_DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
SECTION_TITLES = {"hours": "Hours", "services": "Services", "about": "About", "facts": "Good to know",
                  "photos": "Photos", "contact": "Find us"}


def esc(s):
    return html.escape(str(s if s is not None else ""), quote=True)


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40] or "site"


def lead_slug(lead):
    return "%s-%s" % (slugify(lead["name"]), hashlib.sha1(lead["id"].encode()).hexdigest()[:5])


def digits(phone):
    d = re.sub(r"\D", "", phone or "")
    return "1" + d if len(d) == 10 else d


def safe_url(u):
    u = (u or "").strip()
    return u if re.match(r"^https?://", u, re.I) else ""


def fmt_time(t):
    h, m = (int(x) for x in t.split(":"))
    return "%d%s %s" % (h % 12 or 12, ":%02d" % m if m else "", "am" if h < 12 else "pm")


def parse_hours(hours):
    """[["Monday","Closed"],["Tuesday","10:00-19:00"]] -> list of (day_idx, label, text, opens, closes)."""
    out = []
    for day, spec in hours or []:
        idx = DAY_INDEX.get(day[:3].lower())
        spec = spec.strip()
        if spec.lower() == "closed":
            out.append((idx, day, "Closed", None, None))
            continue
        m = re.match(r"^(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})$", spec)
        if not m:
            raise SystemExit("Hours for %s must look like 10:00-19:00 or Closed (got %r)" % (day, spec))
        out.append((idx, day, "%s – %s" % (fmt_time(m.group(1)), fmt_time(m.group(2))), m.group(1), m.group(2)))
    return out


# ---------------- page sections ----------------
def sec_hours(c, title):
    rows = []
    for idx, day, text, _o, _c in c["hours_parsed"]:
        attr = ' data-day="%d"' % idx if idx is not None else ""
        rows.append("<tr%s><th scope=\"row\">%s</th><td>%s</td></tr>" % (attr, esc(day), esc(text)))
    if rows:
        body = '<table class="hours"><tbody>%s</tbody></table>' % "".join(rows)
    else:
        body = '<p class="todo"><strong>TO GET FROM OWNER:</strong> opening hours</p>'
    return ('<section class="sec sec-hours" aria-labelledby="h-hours"><div class="hours-box">'
            '<h2 id="h-hours">%s</h2>%s</div></section>' % (esc(title), body))


def sec_services(c, title):
    if not c.get("services"):
        return ""
    lis = []
    for s in c["services"]:
        if isinstance(s, str):
            s = {"name": s}
        lis.append('<li><span class="n">%s</span>%s%s</li>' % (
            esc(s["name"]),
            '<span class="price">%s</span>' % esc(s["price"]) if s.get("price") else "",
            '<span class="note">%s</span>' % esc(s["note"]) if s.get("note") else ""))
    return ('<section class="sec sec-services" aria-labelledby="h-services"><h2 id="h-services">%s</h2>'
            '<ul class="svc">%s</ul></section>' % (esc(title), "".join(lis)))


def sec_about(c, title):
    paras = c.get("about")
    if not paras:
        return ""
    if isinstance(paras, str):
        paras = [paras]
    return ('<section class="sec sec-about" aria-labelledby="h-about"><h2 id="h-about">%s</h2>%s</section>'
            % (esc(title), "".join("<p>%s</p>" % esc(p) for p in paras)))


def sec_facts(c, title):
    if not c.get("facts"):
        return ""
    rows = "".join("<div><dt>%s</dt><dd>%s</dd></div>" % (esc(k), esc(v)) for k, v in c["facts"])
    return ('<section class="sec sec-facts" aria-labelledby="h-facts"><h2 id="h-facts">%s</h2><dl class="facts">%s</dl></section>'
            % (esc(title), rows))


def sec_photos(c, title):
    if not c.get("photos_done"):
        return ""
    figs = "".join('<img src="photos/%s" width="%d" height="%d" alt="%s" loading="lazy" decoding="async">'
                   % (esc(p["src"]), p["w"], p["h"], esc(p["alt"])) for p in c["photos_done"])
    return ('<section class="sec sec-photos" aria-labelledby="h-photos"><h2 id="h-photos">%s</h2>'
            '<div class="photos">%s</div></section>' % (esc(title), figs))


def sec_contact(c, title):
    links = ['<a class="btn first" href="%s">Call %s</a>' % (esc(c["tel_href"]), esc(c["phone"])),
             '<a class="btn" href="%s">Send a text</a>' % esc(c["sms_href"]),
             '<a class="btn" href="%s" target="_blank" rel="noopener">Open in Maps</a>' % esc(c["map_href"])]
    for u in c.get("social") or []:
        u = safe_url(u)
        if u:
            label = "Facebook" if "facebook" in u else "Instagram" if "instagram" in u else "Find us online"
            links.append('<a class="btn" href="%s" target="_blank" rel="noopener">%s</a>' % (esc(u), label))
    if c.get("email") and re.match(r"^[^@\s<>\"']+@[^@\s<>\"']+$", c["email"]):
        links.append('<a class="btn" href="mailto:%s">Email us</a>' % esc(c["email"]))
    return ('<section class="sec sec-contact" id="contact" aria-labelledby="h-contact"><h2 id="h-contact">%s</h2>'
            '<address>%s</address><div class="links">%s</div></section>' % (esc(title), esc(c["address"]), "".join(links)))


SECTION_FUNCS = {"hours": sec_hours, "services": sec_services, "about": sec_about, "facts": sec_facts,
                 "photos": sec_photos, "contact": sec_contact}


# ---------------- structured data & assets ----------------
def json_ld(c, base_url, live):
    addr = {"@type": "PostalAddress", "streetAddress": c["address"]}
    m = re.match(r"^(.*?),\s*([^,]+),\s*([A-Z]{2})\s*(\d{5})?", c["address"])
    if m:
        addr.update({"streetAddress": m.group(1), "addressLocality": m.group(2),
                     "addressRegion": m.group(3), "postalCode": m.group(4) or ""})
        addr = {k: v for k, v in addr.items() if v}
    data = {"@context": "https://schema.org", "@type": SCHEMA_TYPES.get(c["type"], "LocalBusiness"),
            "name": c["name"], "telephone": "+" + digits(c["phone"]), "address": addr,
            "url": base_url + "/", "image": base_url + "/og.png"}
    specs = []
    for idx, _d, _t, opens, closes in c["hours_parsed"]:
        if opens and idx is not None:
            specs.append({"@type": "OpeningHoursSpecification", "dayOfWeek": SCHEMA_DAYS[idx],
                          "opens": opens, "closes": closes})
    if specs:
        data["openingHoursSpecification"] = specs
    same = [u for u in (c.get("social") or []) if safe_url(u)]
    if same:
        data["sameAs"] = same
    return '<script type="application/ld+json">%s</script>' % json.dumps(data, ensure_ascii=False).replace("</", "<\\/")


def initials(name):
    words = [w for w in re.findall(r"[A-Za-z0-9]+", name) if w.lower() not in ("the", "and", "of")]
    return ("".join(w[0] for w in words[:2]) or name[:1]).upper()


def favicon_svg(c):
    p = c["design"]["palette"]
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="12" fill="%s"/>'
            '<text x="32" y="43" text-anchor="middle" font-family="Georgia,serif" font-weight="700" font-size="30" fill="%s">%s</text></svg>'
            % (p["accent"], p["on_accent"], esc(initials(c["name"]))))


def font_css_url(c):
    return "https://fonts.googleapis.com/css2?%s&display=swap" % c["design"]["fonts"]["url_params"]


def og_source(c):
    d, p = c["design"], c["design"]["palette"]
    f = d["fonts"]
    return ('<!doctype html><meta charset="utf-8"><link rel="stylesheet" href="%s"><style>'
            'html,body{margin:0}body{width:1200px;height:630px;background:%s;color:%s;font-family:"%s",%s;position:relative;overflow:hidden}'
            '.bar{position:absolute;left:0;top:0;bottom:0;width:36px;background:%s}'
            '.k{position:absolute;left:96px;top:70px;font:700 28px "%s",%s;letter-spacing:.14em;text-transform:uppercase;color:%s}'
            'h1{position:absolute;left:96px;right:60px;top:130px;margin:0;font-family:"%s",%s;font-weight:%s;font-size:132px;line-height:.95;text-transform:uppercase}'
            '.p{position:absolute;left:96px;bottom:64px;font:700 44px "%s",%s}</style>'
            '<div class="bar"></div><div class="k">%s &middot; Milwaukee</div><h1>%s</h1><div class="p">%s</div>'
            % (font_css_url(c), p["bg"], p["ink"], f["body"], f["body_fallback"], p["accent"], f["body"], f["body_fallback"],
               p["muted"], f["head"], f["head_fallback"], f.get("head_weight", 400), f["body"], f["body_fallback"],
               esc(c["type"]), esc(c["name"]), esc(c["phone"])))


def icon_source(c):
    p, f = c["design"]["palette"], c["design"]["fonts"]
    return ('<!doctype html><meta charset="utf-8"><link rel="stylesheet" href="%s"><style>html,body{margin:0}'
            'body{width:180px;height:180px;background:%s;color:%s;display:flex;align-items:center;justify-content:center;'
            'font:%s 84px "%s",%s}</style>%s'
            % (font_css_url(c), p["accent"], p["on_accent"], f.get("head_weight", 400), f["head"], f["head_fallback"], esc(initials(c["name"]))))


# ---------------- build ----------------
def prepare(cfg, site_dir, base_url):
    """Fill in derived fields (links, hours, photos) on a copy of the config."""
    c = dict(cfg)
    dg = digits(c["phone"])
    c["tel_href"] = "tel:+" + dg
    c["sms_href"] = "sms:+" + dg
    c["map_href"] = "https://www.google.com/maps/search/?api=1&query=" + urllib.parse.quote("%s %s" % (c["name"], c["address"]))
    c["hours_parsed"] = parse_hours(c.get("hours"))
    m = re.search(r",\s*([^,]+),\s*([A-Z]{2})\b", c["address"])
    c["city_line"] = "%s, %s" % (m.group(1).strip(), m.group(2)) if m else "Milwaukee, WI"
    return c


def process_photos(c, site_dir, out_dir):
    done = []
    for ph in c.get("photos") or []:
        if not ph.get("alt"):
            raise SystemExit("Photo %s needs alt text (describe it for screen readers)" % ph.get("file"))
        src = os.path.join(site_dir, "photos", ph["file"])
        if not os.path.exists(src):
            raise SystemExit("Photo not found: %s" % src)
        os.makedirs(os.path.join(out_dir, "photos"), exist_ok=True)
        name = slugify(os.path.splitext(ph["file"])[0]) + ".jpg"
        try:
            from PIL import Image, ImageOps
            im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
            im.thumbnail((1600, 1600))
            im.save(os.path.join(out_dir, "photos", name), "JPEG", quality=80, optimize=True, progressive=True)
            w, h = im.size
        except ImportError:
            raise SystemExit("Install Pillow (pip install pillow) so photos are compressed before publishing.")
        done.append({"src": name, "w": w, "h": h, "alt": ph["alt"]})
    return done


def render(cfg, live=False, base_url="https://example.com/site", owner_credit="", photos_done=None):
    c = prepare(cfg, None, base_url)
    c["photos_done"] = photos_done or []
    d = c["design"]
    titles = dict(SECTION_TITLES, **(d.get("section_titles") or {}))
    sections = "\n".join(s for s in (SECTION_FUNCS[k](c, titles[k]) for k in d["section_order"]) if s)

    layout_dir = os.path.join(HERE, "layouts", d["layout"])
    body = open(os.path.join(layout_dir, "body.html"), encoding="utf-8").read()
    layout_css = open(os.path.join(layout_dir, "layout.css"), encoding="utf-8").read()
    common_css = open(os.path.join(HERE, "common.css"), encoding="utf-8").read()
    shell = open(os.path.join(HERE, "shell.html"), encoding="utf-8").read()

    p, f = d["palette"], d["fonts"]
    palette_css = ":root{%s--head-font:'%s',%s;--body-font:'%s',%s}" % (
        "".join("--%s:%s;" % (k, v) for k, v in p.items()), f["head"], f["head_fallback"], f["body"], f["body_fallback"])

    lines = d.get("hero_lines") or c["name"].split()
    hero_lines_html = "".join('<span class="l">%s</span>' % esc(l) for l in lines)
    if " ".join(lines).lower() != c["name"].lower():
        raise SystemExit("design.hero_lines must spell the business name exactly")

    description = c.get("description") or "%s – %s in %s. Call %s." % (c["name"], c["type"].lower(), c["city_line"], c["phone"])
    kicker = c.get("kicker") or "%s · %s" % (c["type"], c["city_line"])
    credit = c.get("credit", owner_credit)
    values = {
        "name": esc(c["name"]), "phone": esc(c["phone"]), "address": esc(c["address"]), "headline": esc(c["headline"]),
        "kicker": esc(kicker), "tel_href": esc(c["tel_href"]), "map_href": esc(c["map_href"]),
        "hero_lines_html": hero_lines_html, "sections": sections,
        "credit_html": "<p>%s</p>" % esc(credit) if credit else "", "year": str(datetime.date.today().year),
    }
    body = re.sub(r"\{\{(\w+)\}\}", lambda m: values[m.group(1)], body)

    if live:
        robots, banner = "", ""
        canonical = '<link rel="canonical" href="%s/">' % esc(base_url)
    else:
        robots = '<meta name="robots" content="noindex,nofollow">'
        canonical = ""
        msg = "SAMPLE DESIGN · pretend business, not a real shop" if c.get("sample") else \
            "PREVIEW for %s · not their official website yet" % c["name"]
        banner = '<div class="banner">%s</div>' % esc(msg)

    title = c.get("title") or "%s | %s, %s" % (c["name"], c["type"], c["city_line"])
    social = "\n".join('<meta %s="%s" content="%s">' % (a, k, esc(v)) for a, k, v in [
        ("property", "og:type", "website"), ("property", "og:title", title), ("property", "og:description", description),
        ("property", "og:url", base_url + "/"), ("property", "og:image", base_url + "/og.png"),
        ("property", "og:image:width", "1200"), ("property", "og:image:height", "630"),
        ("name", "twitter:card", "summary_large_image")])
    values2 = {
        "title": esc(title), "description": esc(description), "robots": robots, "theme_color": esc(p["panel"]),
        "canonical": canonical, "social_meta": social, "font_url": esc(font_css_url(c)),
        "css": common_css + palette_css + layout_css, "jsonld": json_ld(c, base_url, live),
        "layout": esc(d["layout"]), "banner": banner, "body": body,
        "tel_href": esc(c["tel_href"]), "map_href": esc(c["map_href"]),
    }
    return re.sub(r"\{\{(\w+)\}\}", lambda m: values2[m.group(1)], shell)


def page_404(c):
    p = c["design"]["palette"]
    f = c["design"]["fonts"]
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<meta name="robots" content="noindex"><title>Page not found | %s</title><link rel="stylesheet" href="%s"><style>'
            'body{margin:0;min-height:100vh;display:grid;place-content:center;padding:24px;background:%s;color:%s;font-family:"%s",%s;font-size:1.1rem}'
            'h1{font-family:"%s",%s;font-size:2.4rem;margin:0 0 12px}a{display:inline-block;min-height:48px;line-height:48px;padding:0 20px;background:%s;color:%s;font-weight:700;text-decoration:none}'
            ':focus-visible{outline:3px solid %s;outline-offset:3px}</style></head><body><main><h1>Page not found</h1>'
            '<p>That page isn\'t here. Try the main page.</p><a href="./">Back to %s</a></main></body></html>'
            % (esc(c["name"]), esc(font_css_url(c)), p["bg"], p["ink"], f["body"], f["body_fallback"], f["head"], f["head_fallback"],
               p["accent"], p["on_accent"], p["accent"], esc(c["name"])))


def collect_to_get(c, live_blockers=None):
    """Everything still needed from the owner. Returns (items, blocking_items)."""
    items, blocking = [], []
    if not c.get("hours"):
        blocking.append("Opening hours for every day of the week (and any holiday closures)")
    if not c.get("photos"):
        shots = SHOT_LISTS.get(c["type"], SHOT_LISTS["_default"])
        items.append("Photos, taken on a phone in daylight, landscape: " + "; ".join(shots))
    if not c.get("about"):
        items.append("2-3 sentences in the owner's own words: what they're known for, how long they've been open, who their customers are")
    if not c.get("facts"):
        items.append("Walk-ins or appointments? Parking? Payment types accepted? Languages spoken? Any specials/prices they want shown?")
    for u in c.get("unconfirmed") or []:
        blocking.append("Confirm with the owner that the %s shown are right" % u)
    blocking += c.get("to_get") or []
    if not c.get("email"):
        items.append("Email address (optional) and Facebook/Instagram links if they have them")
    return items, blocking


def write_checklist(c, site_dir, items, blocking):
    path = os.path.join(site_dir, "TO-GET-FROM-OWNER.md")
    lines = ["# TO GET FROM OWNER - %s\n" % c["name"]]
    if c.get("sample"):
        lines.append("_This is a SAMPLE (pretend business) - nothing here is a real owner's information._\n")
    lines.append("## Needed before going live (blocks `--live`)")
    lines += ["- [ ] " + b for b in blocking] or ["- (nothing)"]
    lines.append("\n## Needed to make the site better")
    lines += ["- [ ] " + i for i in items] or ["- (nothing)"]
    lines.append("\n## Before going live\n- [ ] Owner has seen the demo link and said OK in writing (text is fine)\n"
                 "- [ ] Every detail confirmed by the owner (phone, address, hours, services)\n"
                 "- [ ] Run again with `--live`; fix anything the checks report")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return path


def validate_config(cfg):
    errs = []
    for k in ("slug", "name", "type", "phone", "address", "headline", "design"):
        if not cfg.get(k):
            errs.append("site.json is missing '%s'" % k)
    d = cfg.get("design") or {}
    for k in ("layout", "fonts", "palette", "palette_reason", "hero", "section_order", "signature"):
        if not d.get(k):
            errs.append("design.%s is missing" % k)
    f = d.get("fonts") or {}
    for k in ("head", "body", "url_params", "head_fallback", "body_fallback"):
        if not f.get(k):
            errs.append("design.fonts.%s is missing" % k)
    if f.get("head", "").lower() in checks.BANNED_HEADING_FONTS:
        errs.append("%s is not allowed as a heading font" % f["head"])
    if d.get("layout") and not os.path.isdir(os.path.join(HERE, "layouts", d["layout"])):
        errs.append("unknown layout %r (have: %s)" % (d["layout"], ", ".join(sorted(os.listdir(os.path.join(HERE, "layouts"))))))
    if d.get("palette"):
        errs += checks.check_palette(d["palette"], not d.get("accent_is_decorative"))
    if "contact" not in (d.get("section_order") or []):
        errs.append("design.section_order must include 'contact'")
    return errs


def scaffold(lead_id, csv_path):
    with open(csv_path, newline="", encoding="utf-8") as f:
        lead = next((r for r in csv.DictReader(f) if r["id"] == lead_id), None)
    if not lead:
        raise SystemExit("Lead %r not found in %s" % (lead_id, csv_path))
    slug = lead_slug(lead)
    d = os.path.join(ROOT, "sites", slug)
    os.makedirs(d, exist_ok=True)
    cfg = {"slug": slug, "name": lead["name"], "type": lead["type"], "phone": lead["phone"], "address": lead["address"],
           "social": [s.strip() for s in lead.get("social", "").split("|") if s.strip()],
           "headline": "TODO", "hours": None, "services": [], "unconfirmed": [], "to_get": [],
           "design": {"layout": "TODO", "fonts": {}, "palette": {}, "palette_reason": "", "hero": "", "section_order": [], "signature": ""}}
    sj = os.path.join(d, "site.json")
    if not os.path.exists(sj):
        json.dump(cfg, open(sj, "w", encoding="utf-8"), indent=2)
    bp = os.path.join(d, "brief.md")
    if not os.path.exists(bp):
        shutil.copy(os.path.join(HERE, "BRIEF_TEMPLATE.md"), bp)
        t = open(bp, encoding="utf-8").read().replace("{NAME}", lead["name"])
        open(bp, "w", encoding="utf-8").write(t)
    print("Scaffolded sites/%s/ (site.json + brief.md). Next: write the brief, pick the design, then build." % slug)
    return slug


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("site_json", nargs="?", help="path to sites/<slug>/site.json")
    ap.add_argument("--scaffold", metavar="LEAD_ID", help="create starter brief + site.json for a lead")
    ap.add_argument("--csv", default=os.path.join(ROOT, "data", "leads.csv"))
    ap.add_argument("--out", default=os.path.join(ROOT, "docs"))
    ap.add_argument("--log", default=os.path.join(ROOT, "design-log.json"))
    ap.add_argument("--export", help="write a standalone site into this folder (for a client's own domain)")
    ap.add_argument("--cname", help="custom domain, written to a CNAME file (with --export)")
    ap.add_argument("--live", action="store_true", help="remove demo banner/noindex (ONLY with the owner's OK)")
    ap.add_argument("--skip-assets", action="store_true", help="don't render og.png / apple-touch-icon.png")
    args = ap.parse_args(argv)

    if args.scaffold:
        scaffold(args.scaffold, args.csv)
        return 0
    if not args.site_json:
        ap.error("give the path to a site.json (or use --scaffold)")

    site_dir = os.path.dirname(os.path.abspath(args.site_json))
    cfg = json.load(open(args.site_json, encoding="utf-8"))
    errs = validate_config(cfg)
    errs += checks.check_brief(os.path.join(site_dir, "brief.md"))
    pages_base = "https://yunuhkei.github.io/local-sites"
    owner_credit = ""
    cpath = os.path.join(ROOT, "config.json")
    if os.path.exists(cpath):
        conf = json.load(open(cpath, encoding="utf-8"))
        pages_base, owner_credit = conf.get("pages_base", pages_base), conf.get("credit", "")
    if errs:
        print("Cannot build - fix these first:\n  - " + "\n  - ".join(errs), file=sys.stderr)
        return 1

    order = [s for s in cfg["design"]["section_order"]]
    entry = checks.design_entry(cfg, order)
    log = checks.load_log(args.log)
    bad = checks.design_conflicts(entry, log["sites"])
    if bad:
        print("Design too similar to earlier sites (rule: share at most ONE of layout/fonts/palette/hero/section order):",
              file=sys.stderr)
        for slug, shared in bad:
            print("  - shares %s with %s" % (", ".join(shared), slug), file=sys.stderr)
        return 1

    items, blocking = collect_to_get(cfg)
    if args.live and (blocking or cfg.get("sample")):
        print("Cannot go live yet:\n  - " + "\n  - ".join(blocking + (["this is a SAMPLE, not a real business"] if cfg.get("sample") else [])),
              file=sys.stderr)
        return 1

    slug = cfg["slug"]
    out_dir = args.export or os.path.join(args.out, slug)
    os.makedirs(out_dir, exist_ok=True)
    base_url = ("https://" + args.cname.strip()) if args.cname else "%s/%s" % (pages_base, slug)

    photos_done = process_photos(cfg, site_dir, out_dir)
    page = render(cfg, live=args.live, base_url=base_url, owner_credit=owner_credit, photos_done=photos_done)
    page_errs = checks.scan_page(page, live=args.live)
    if page_errs:
        print("Page failed the design rules:\n  - " + "\n  - ".join(page_errs), file=sys.stderr)
        return 1

    c = prepare(cfg, site_dir, base_url)
    for name, content in (("index.html", page), ("404.html", page_404(c)), ("favicon.svg", favicon_svg(c))):
        open(os.path.join(out_dir, name), "w", encoding="utf-8").write(content)
    if args.cname:
        open(os.path.join(out_dir, "CNAME"), "w").write(args.cname.strip() + "\n")
        open(os.path.join(out_dir, ".nojekyll"), "w").close()

    if not args.skip_assets:
        build_dir = os.path.join(site_dir, "_build")
        os.makedirs(build_dir, exist_ok=True)
        open(os.path.join(build_dir, "og.html"), "w", encoding="utf-8").write(og_source(c))
        open(os.path.join(build_dir, "icon.html"), "w", encoding="utf-8").write(icon_source(c))
        r = subprocess.run(["node", os.path.join(HERE, "render_assets.js"), build_dir, out_dir],
                           capture_output=True, text=True)
        if r.returncode != 0:
            print("WARNING: could not render og.png/apple-touch-icon.png:\n" + r.stderr[-400:], file=sys.stderr)

    checklist = write_checklist(c, site_dir, items, blocking)
    if not args.export:
        checks.save_log(args.log, log, entry)
    print("Built %s site for %s -> %s" % ("LIVE" if args.live else "DEMO", cfg["name"], out_dir))
    print("TO GET FROM OWNER list: %s (%d must-haves, %d nice-to-haves)" % (os.path.relpath(checklist, ROOT), len(blocking), len(items)))
    if not args.live:
        print("Demo link once published: %s/" % base_url)
    return 0


if __name__ == "__main__":
    sys.exit(main())
