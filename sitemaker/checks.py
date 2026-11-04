"""Automatic design-rule checks. Used by make_site.py (blocking) and qa.py (reporting)."""
import html as htmllib
import json
import os
import re

BANNED_WORDS = ["elevate", "seamless", "unlock", "discover", "experience the difference", "passion",
                "journey", "cutting-edge", "cutting edge", "world-class", "world class",
                "one-stop shop", "one stop shop", "look no further"]
BANNED_HEADING_FONTS = {"inter", "roboto", "poppins"}
FAKE_PROOF = ["trusted by", "testimonial", "award-winning", "award winning", "5-star", "five-star",
              "★", "⭐", "lorem ipsum"]
EMOJI_RE = re.compile("[\U0001F300-\U0001FAFF☀-➿⭐✨️]")
BRIEF_HEADINGS = ["Customers", "Neighborhood", "Vibe", "References", "Palette", "Type", "Layout",
                  "Signature"]
SHARE_KEYS = ["layout", "fonts", "palette", "hero", "section_order"]


# ---------- color contrast (WCAG) ----------
def _lin(c):
    c /= 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def luminance(hexcolor):
    h = hexcolor.lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def check_palette(p, accent_text_on_bg=True):
    """Return a list of error strings. Needs bg, ink, muted, accent, on_accent, panel, on_panel."""
    need = ["bg", "ink", "muted", "accent", "on_accent", "panel", "on_panel"]
    errs = ["palette is missing '%s'" % k for k in need if k not in p]
    if errs:
        return errs
    pairs = [("ink", "bg", 4.5), ("muted", "bg", 4.5), ("on_accent", "accent", 4.5),
             ("on_panel", "panel", 4.5)]
    if accent_text_on_bg:                      # accent used for text/lines on the page background
        pairs.append(("accent", "bg", 3.0))
    for fg, bg, need_ratio in pairs:
        ratio = contrast(p[fg], p[bg])
        if ratio < need_ratio:
            errs.append("contrast %s on %s is %.2f (needs %.1f)" % (fg, bg, ratio, need_ratio))
    return errs


# ---------- brief ----------
def check_brief(path):
    if not os.path.exists(path):
        return ["missing design brief: %s (write it BEFORE building)" % path]
    text = open(path, encoding="utf-8").read()
    errs = []
    for h in BRIEF_HEADINGS:
        if not re.search(r"^##\s*%s\b" % h, text, re.M | re.I):
            errs.append("brief is missing the '## %s' section" % h)
    m = re.search(r"^##\s*References\b(.*?)(?=^##|\Z)", text, re.M | re.I | re.S)
    if m and len(re.findall(r"^\s*[-*]\s+\S", m.group(1), re.M)) < 3:
        errs.append("brief needs 3 real-world references (bullets) under '## References'")
    if "{" in text and "}" in text and re.search(r"\{[^}]{3,}\}", text):
        errs.append("brief still has {template placeholders}")
    if len(text) < 600:
        errs.append("brief is too short to guide a design")
    return errs


# ---------- design log ----------
def design_entry(cfg, order):
    d = cfg["design"]
    p = d["palette"]
    return {
        "slug": cfg["slug"], "business": cfg["name"], "layout": d["layout"],
        "fonts": [d["fonts"]["head"], d["fonts"]["body"]],
        "palette": [p["bg"].lower(), p["ink"].lower(), p["accent"].lower()],
        "hero": d["hero"], "section_order": order, "signature": d["signature"],
    }


def shared_attributes(a, b):
    shared = []
    if a["layout"] == b["layout"]:
        shared.append("layout")
    if a["fonts"][0] == b["fonts"][0] or a["fonts"][1] == b["fonts"][1]:
        shared.append("fonts")
    if len(set(a["palette"]) & set(b["palette"])) >= 2:
        shared.append("palette")
    if a["hero"] == b["hero"]:
        shared.append("hero")
    if a["section_order"] == b["section_order"]:
        shared.append("section_order")
    return shared


def design_conflicts(entry, log_sites):
    """Sites that share MORE than one attribute with this one (rule: at most one)."""
    bad = []
    for other in log_sites:
        if other["slug"] == entry["slug"]:
            continue
        s = shared_attributes(entry, other)
        if len(s) > 1:
            bad.append((other["slug"], s))
    return bad


def load_log(path):
    if os.path.exists(path):
        return json.load(open(path, encoding="utf-8"))
    return {"rule": "A new site may share at most ONE of: layout, fonts, palette, hero, section_order "
                    "with any earlier site.", "sites": []}


def save_log(path, log, entry):
    log["sites"] = [s for s in log["sites"] if s["slug"] != entry["slug"]] + [entry]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)
        f.write("\n")


# ---------- page scan ----------
def visible_text(page):
    t = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", page)
    t = re.sub(r"(?s)<[^>]+>", " ", t)
    return htmllib.unescape(re.sub(r"\s+", " ", t))


def scan_page(page, live=False):
    errs = []
    text = visible_text(page).lower()
    for w in BANNED_WORDS:
        if re.search(r"\b%s" % re.escape(w), text):
            errs.append("banned copy word/phrase: %r" % w)
    for w in FAKE_PROOF:
        if w in text:
            errs.append("fake-proof/placeholder text: %r" % w)
    if EMOJI_RE.search(visible_text(page)):
        errs.append("emoji found (not allowed as icons)")
    if re.search(r'href=["\']#["\']', page) or 'href=""' in page:
        errs.append('empty/"#" link found')
    for bad in ("backdrop-filter", "blur("):
        if bad in page:
            errs.append("banned effect: %s" % bad)
    if live and "TO GET FROM OWNER" in page:
        errs.append("live site still contains TO GET FROM OWNER placeholders")
    h1 = len(re.findall(r"<h1[\s>]", page))
    if h1 != 1:
        errs.append("page needs exactly one <h1> (found %d)" % h1)
    last = 0
    for lvl in map(int, re.findall(r"<h([1-6])[\s>]", page)):
        if lvl > last + 1:
            errs.append("heading level jumps from h%d to h%d" % (last, lvl))
        last = lvl
    for img in re.findall(r"<img\b[^>]*>", page):
        if not re.search(r'\balt="[^"]+"', img):
            errs.append("image without alt text: %s" % img[:60])
    if ":focus-visible" not in page:
        errs.append("no :focus-visible style (keyboard users need a visible focus)")
    return errs
