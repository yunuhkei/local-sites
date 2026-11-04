#!/usr/bin/env python3
"""Make a clean, mobile-friendly one-page website for a business.

Examples:
    # from a lead in data/leads.csv (a private-looking folder name is made for you)
    python3 sitemaker/make_site.py --lead osm-node-123456

    # from a hand-edited config file
    python3 sitemaker/make_site.py --config sites/demo-barbershop.json

    # after the owner says YES and pays: a standalone folder for their own domain
    python3 sitemaker/make_site.py --config sites/xyz.json --live --export out/xyz --cname www.xyz.com

By default every site is a DEMO: it shows a "preview" banner and tells search
engines not to list it. Only use --live after the owner has OK'd it.
Standard library only; nothing to install.
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
import sys
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TEMPLATES = os.path.join(HERE, "templates")

FONT_URLS = {
    "barber": "https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Oswald:wght@500;700&display=swap",
    "salon": "https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Playfair+Display:wght@600;700&display=swap",
    "food": "https://fonts.googleapis.com/css2?family=Fraunces:wght@600;700&family=Inter:wght@400;600;700&display=swap",
    "service": "https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Poppins:wght@600;700&display=swap",
}
THEME_COLORS = {"barber": "#000000", "salon": "#ffffff", "food": "#b3361b", "service": "#0f2a43"}
SERVICES_TITLE = {"barber": "Services", "salon": "Services", "food": "What we serve", "service": "What we do"}

# Business type label (from the lead finder) -> template
TEMPLATE_FOR = {
    "Barbershop": "barber",
    "Hair salon": "salon", "Nail salon": "salon", "Beauty salon": "salon", "Massage": "salon",
    "Tattoo studio": "salon", "Pet grooming": "salon", "Florist": "salon",
    "Restaurant": "food", "Fast food / takeout": "food", "Cafe": "food", "Food truck": "food",
    "Bakery": "food", "Butcher / meat market": "food", "Deli": "food",
}

# Starter copy per type. Review with the owner before going live - never assume it is accurate.
DEFAULTS = {
    "Barbershop": ("Sharp cuts and clean shaves in your Milwaukee neighborhood.",
                   [("Haircut", "Classic and modern cuts"), ("Beard trim", "Shaped and cleaned up"),
                    ("Line-up", "Crisp edges"), ("Kids' cuts", "")]),
    "Hair salon": ("Cut, color and style - right here in Milwaukee.",
                   [("Haircut & style", ""), ("Color", ""), ("Blowouts", ""), ("Treatments", "")]),
    "Nail salon": ("Beautiful nails in a relaxing space.",
                   [("Manicure", ""), ("Pedicure", ""), ("Gel & acrylic", ""), ("Nail art", "")]),
    "Beauty salon": ("Look and feel your best.",
                     [("Facials", ""), ("Waxing", ""), ("Lashes & brows", ""), ("Makeup", "")]),
    "Restaurant": ("Good food, made fresh, right in the neighborhood.",
                   [("Dine in", ""), ("Takeout", ""), ("Catering", ""), ("Daily specials", "")]),
    "Fast food / takeout": ("Quick, tasty and ready when you are.",
                            [("Takeout", ""), ("Combos", ""), ("Catering", "")]),
    "Cafe": ("Coffee, treats and a good place to sit.",
             [("Coffee & espresso", ""), ("Fresh pastries", ""), ("Breakfast & lunch", "")]),
    "Food truck": ("Fresh street food - find us around Milwaukee.",
                   [("Our menu", ""), ("Events & catering", ""), ("Where to find us", "")]),
    "Bakery": ("Baked fresh, made with care.",
               [("Breads", ""), ("Cakes & custom orders", ""), ("Pastries", "")]),
    "Dry cleaner": ("Dry cleaning and laundry you can count on.",
                    [("Dry cleaning", ""), ("Wash & fold", ""), ("Alterations", ""), ("Pickup & delivery", "")]),
    "Laundry / cleaner": ("Clean clothes, done right.",
                          [("Wash & fold", ""), ("Dry cleaning", ""), ("Alterations", "")]),
    "Auto repair": ("Honest auto repair from a local shop.",
                    [("Oil changes", ""), ("Brakes", ""), ("Tires", ""), ("Diagnostics", "")]),
    "Car wash": ("Get your car sparkling clean.",
                 [("Exterior wash", ""), ("Interior cleaning", ""), ("Detailing", "")]),
    "Tire shop": ("Tires, mounting and repair.",
                  [("New & used tires", ""), ("Flat repair", ""), ("Rotation & balancing", "")]),
    "Daycare": ("A safe, caring place for your little ones to learn and play.",
                [("Full-time care", ""), ("Part-time care", ""), ("Learning activities", ""), ("Meals & snacks", "")]),
}
GENERIC = ("Friendly, reliable local service in Milwaukee.",
           [("Call to learn more", "")])

DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
PHOTO_CAPTIONS = ["Your photo here", "Add a favorite", "Show your work", "Your space", "Happy customers", "Your photo here"]


def esc(s):
    return html.escape(str(s or ""), quote=True)


def slugify(text):
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:40] or "site"


def lead_slug(lead):
    """Name + short hash, so demo links are not guessable by strangers."""
    return "%s-%s" % (slugify(lead["name"]), hashlib.sha1(lead["id"].encode()).hexdigest()[:5])


def digits(phone):
    d = re.sub(r"\D", "", phone or "")
    if len(d) == 10:
        d = "1" + d
    return d


def safe_url(u):
    u = (u or "").strip()
    return u if re.match(r"^https?://", u, re.I) else ""


def load_lead(csv_path, lead_id):
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["id"] == lead_id:
                return row
    raise SystemExit("Lead %r not found in %s" % (lead_id, csv_path))


def pick_template(type_label, override=None):
    if override:
        if override not in FONT_URLS:
            raise SystemExit("Unknown template %r. Choose from: %s" % (override, ", ".join(FONT_URLS)))
        return override
    return TEMPLATE_FOR.get(type_label, "service")


def render(cfg, live=False, photo_files=None, owner_credit=""):
    """Return the finished HTML for one site. cfg keys: name, type, phone, address, ..."""
    name = cfg["name"].strip()
    type_label = cfg.get("type") or "Local business"
    template = pick_template(type_label, cfg.get("template"))
    tagline_default, services_default = DEFAULTS.get(type_label, GENERIC)

    tagline = cfg.get("tagline") or tagline_default
    services = cfg.get("services")
    if not services:
        services = [{"name": n, "desc": d} for n, d in services_default]
    phone = (cfg.get("phone") or "").strip()
    address = (cfg.get("address") or "").strip()
    dg = digits(phone)

    tel_href = "tel:+%s" % dg if dg else "#contact"
    sms_href = "sms:+%s" % dg if dg else "#contact"
    where = address or ("%s Milwaukee WI" % name)
    map_href = "https://www.google.com/maps/search/?api=1&query=" + urllib.parse.quote(name + " " + where if address else where)
    city_line = "Milwaukee, WI"
    m = re.search(r",\s*([^,]+),\s*([A-Z]{2})\b", address)
    if m:
        city_line = "%s, %s" % (m.group(1).strip(), m.group(2))

    about = cfg.get("about") or (
        "%s is a local %s serving the Milwaukee community. Call or text us to book, ask a question, "
        "or find out more." % (name, type_label.lower()))

    # --- services
    items = []
    for s in services:
        if isinstance(s, str):
            s = {"name": s}
        price = '<span class="price">%s</span>' % esc(s["price"]) if s.get("price") else ""
        desc = '<span class="d">%s</span>' % esc(s["desc"]) if s.get("desc") else ""
        items.append("        <li><strong>%s %s</strong>%s</li>" % (esc(s["name"]), price, desc))
    services_html = "\n".join(items)

    # --- hours
    rows = []
    for entry in cfg.get("hours") or []:
        day, text = entry[0], entry[1]
        idx = next((i for i, d in enumerate(DAYS) if day[:3].lower() == d.lower()), None)
        attr = ' data-day="%d"' % idx if idx is not None else ""
        rows.append("        <tr%s><td>%s</td><td>%s</td></tr>" % (attr, esc(day), esc(text)))
    if not rows:
        rows.append('        <tr><td>Hours</td><td>Call for today\'s hours</td></tr>')
    hours_html = "\n".join(rows)

    # --- photos (real files if provided; placeholders only on demos)
    photo_files = photo_files or []
    if photo_files:
        figs = ['        <figure><img src="photos/%s" alt="%s photo" loading="lazy"></figure>'
                % (urllib.parse.quote(p), esc(name)) for p in photo_files]
    elif not live:
        figs = ['        <figure><div class="ph">%s</div></figure>' % esc(c) for c in PHOTO_CAPTIONS]
    else:
        figs = []
    photos_section = ""
    if figs:
        photos_section = ('  <section class="block alt" id="photos">\n    <div class="wrap">\n      <h2>Photos</h2>\n'
                          '      <div class="gallery">\n%s\n      </div>\n    </div>\n  </section>' % "\n".join(figs))

    # --- extra buttons (social, email)
    extra = []
    for u in cfg.get("social") or []:
        u = safe_url(u)
        if u:
            label = "Facebook" if "facebook" in u else "Instagram" if "instagram" in u else "Find us online"
            extra.append('        <a class="btn btn-ghost" href="%s" target="_blank" rel="noopener">%s</a>' % (esc(u), label))
    if cfg.get("email") and re.match(r"^[^@\s<>\"']+@[^@\s<>\"']+$", cfg["email"]):
        extra.append('        <a class="btn btn-ghost" href="mailto:%s">Email us</a>' % esc(cfg["email"]))

    description = "%s - %s in %s. Call %s." % (name, type_label.lower(), city_line, phone) if phone else \
        "%s - %s in %s." % (name, type_label.lower(), city_line)

    jsonld = ""
    if live:
        data = {"@context": "https://schema.org", "@type": "LocalBusiness", "name": name,
                "telephone": "+" + dg if dg else None, "description": description,
                "address": {"@type": "PostalAddress", "streetAddress": address} if address else None}
        data = {k: v for k, v in data.items() if v}
        jsonld = '<script type="application/ld+json">%s</script>' % json.dumps(data).replace("</", "<\\/")

    credit = cfg.get("credit", owner_credit)
    credit_html = "<p>%s</p>" % esc(credit) if credit else ""

    if live:
        robots, demo_banner, demo_class = "", "", ""
    else:
        robots = '<meta name="robots" content="noindex,nofollow">'
        demo_banner = ('<div class="demo-bar">Preview made for %s &mdash; not their official website yet</div>' % esc(name))
        demo_class = " is-demo"

    base_css = open(os.path.join(TEMPLATES, "base.css"), encoding="utf-8").read()
    theme_css = open(os.path.join(TEMPLATES, template + ".css"), encoding="utf-8").read()
    page = open(os.path.join(TEMPLATES, "base.html"), encoding="utf-8").read()

    values = {
        "title": "%s | %s in %s" % (name, type_label, city_line),
        "description": description, "robots": robots, "theme_color": THEME_COLORS[template],
        "font_url": FONT_URLS[template], "base_css": base_css, "theme_css": theme_css,
        "jsonld": jsonld, "template": template, "demo_class": demo_class, "demo_banner": demo_banner,
        "name": name, "tel_href": tel_href, "sms_href": sms_href, "map_href": map_href,
        "type_label": type_label, "city_line": city_line, "tagline": tagline,
        "phone": phone or "us", "services_title": SERVICES_TITLE[template], "services_html": services_html,
        "about": about, "hours_html": hours_html, "photos_section": photos_section,
        "address": address or "Milwaukee, WI", "extra_buttons": "\n".join(extra),
        "year": datetime.date.today().year, "credit_html": credit_html,
    }
    # raw (already-escaped/trusted) pieces vs. plain text that must be escaped:
    raw = {"robots", "base_css", "theme_css", "jsonld", "demo_banner", "services_html", "hours_html",
           "photos_section", "extra_buttons", "credit_html", "template", "demo_class", "font_url",
           "theme_color", "year"}
    url_attrs = {"tel_href", "sms_href", "map_href"}

    def fill(match):
        key = match.group(1)
        v = values[key]
        if key in raw:
            return str(v)
        if key in url_attrs:
            return esc(v)
        return esc(v)

    return re.sub(r"\{\{(\w+)\}\}", fill, page)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--lead", help="lead id from data/leads.csv")
    src.add_argument("--config", help="path to a site .json file")
    ap.add_argument("--csv", default=os.path.join(ROOT, "data", "leads.csv"))
    ap.add_argument("--out", default=os.path.join(ROOT, "docs"), help="folder that GitHub Pages publishes (default docs/)")
    ap.add_argument("--export", help="write a standalone site into THIS folder (for a client's own domain)")
    ap.add_argument("--template", choices=sorted(FONT_URLS), help="force a template")
    ap.add_argument("--live", action="store_true", help="remove demo banner/noindex (ONLY with the owner's OK)")
    ap.add_argument("--cname", help="custom domain to write into a CNAME file (use with --export)")
    args = ap.parse_args(argv)

    cfg, slug, cfg_dir = {}, None, None
    if args.lead:
        lead = load_lead(args.csv, args.lead)
        slug = lead_slug(lead)
        cfg = {"name": lead["name"], "type": lead["type"], "phone": lead["phone"], "address": lead["address"],
               "social": [s.strip() for s in lead.get("social", "").split("|") if s.strip()]}
        override = os.path.join(ROOT, "sites", slug + ".json")      # optional hand edits
        if os.path.exists(override):
            with open(override, encoding="utf-8") as f:
                cfg.update(json.load(f))
            cfg_dir = os.path.join(ROOT, "sites", slug)
    else:
        with open(args.config, encoding="utf-8") as f:
            cfg = json.load(f)
        slug = cfg.get("slug") or slugify(cfg["name"])
        cfg_dir = os.path.join(os.path.dirname(os.path.abspath(args.config)), slug)
    if args.template:
        cfg["template"] = args.template

    owner_credit = ""
    cfg_path = os.path.join(ROOT, "config.json")
    if os.path.exists(cfg_path):
        with open(cfg_path, encoding="utf-8") as f:
            owner_credit = json.load(f).get("credit", "")

    out_dir = args.export or os.path.join(args.out, slug)
    os.makedirs(out_dir, exist_ok=True)

    # photos: drop image files in sites/<slug>/ ; they are copied next to index.html
    photo_files = []
    if cfg_dir and os.path.isdir(cfg_dir):
        os.makedirs(os.path.join(out_dir, "photos"), exist_ok=True)
        for fn in sorted(os.listdir(cfg_dir)):
            if re.search(r"\.(jpe?g|png|webp)$", fn, re.I):
                shutil.copy(os.path.join(cfg_dir, fn), os.path.join(out_dir, "photos", fn))
                photo_files.append(fn)

    page = render(cfg, live=args.live, photo_files=photo_files, owner_credit=owner_credit)
    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(page)
    if args.cname:
        with open(os.path.join(out_dir, "CNAME"), "w", encoding="utf-8") as f:
            f.write(args.cname.strip() + "\n")
        open(os.path.join(out_dir, ".nojekyll"), "w").close()

    print("Made %s site for %s -> %s" % ("LIVE" if args.live else "DEMO", cfg["name"], out_dir))
    if not args.export:
        print("Demo link (after you publish): https://<your-github-name>.github.io/local-sites/%s/" % slug)
    if args.live:
        print("REMINDER: only publish a live site with the owner's OK, and check every detail with them first.")
    else:
        print("Demo mode: shows a 'preview' banner and is hidden from Google. Check details with the owner.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
