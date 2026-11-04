"""Clean and score leads: drop things you can't sell a website to, rank the rest.

Used by find_leads.py (every weekly run) and rank.py (Top-20 list).
Nothing here uses the internet.
"""
import datetime
import json
import math
import os
import re

def _home():
    """Where distances are measured from: config.json "home" (ZIP 53218 center by default)."""
    try:
        h = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")))["home"]
        return float(h["lat"]), float(h["lon"])
    except (OSError, KeyError, ValueError, TypeError):
        return 43.14, -88.00


CENTER = _home()

GOVERNMENT = re.compile(r"\b(city of|county|village of|town of|state of|department|dept|police|fire (dept|department|station)|"
                        r"library|post office|courthouse|dmv|public school|school district|elementary|middle school|"
                        r"high school|head start|university|college|milwaukee public|mps|park concession|concession stand)\b", re.I)
CHURCH = re.compile(r"\b(church|chapel|cathedral|parish|ministr(y|ies)|temple|mosque|synagogue|baptist|lutheran|"
                    r"methodist|catholic|congregation|diocese|archdiocese)\b", re.I)
CLOSED = re.compile(r"\bclosed\b|\(former|\bformerly\b|\bex-|permanently|moved to|out of business", re.I)
_CHAIN_NAMES = (
    r"mcdonald|burger king|wendy'?s|subway|starbucks|dunkin|kfc|taco bell|pizza hut|domino'?s|papa john|little caesar|"
    r"culver|hardee|popeyes?|jimmy john|arby|chipotle|panera|jiffy lube|midas auto|pep boys|firestone|goodyear|meineke|"
    r"valvoline|napa auto|autozone|o'?reilly|advance auto|discount tire|walmart|kohl'?s|great clips|sport clips|"
    r"supercuts|fantastic sams|regis salon|planet fitness|mister car wash|7-eleven|kwik trip|"
    r"cvs|walgreens|dollar general|dollar tree|aldi|pick 'n save|metro market|"
    r"sendik|woodman|jersey mike|five guys|qdoba|noodles & company|pita pit|church'?s chicken|white castle|"
    r"dairy queen|tim hortons|caribou coffee|peet'?s|biggby|einstein bro|bruegger|great harvest|kumon|goddard school|"
    r"kindercare|primrose|learning care|la petite|tutor time|bright horizons|sylvan|mathnasium|"
    r"cafe zupas|martinizing|national muffler|maytag laundry|ulta|sally beauty|sephora|jcpenney|macy'?s|menards|home depot|lowe'?s|ace hardware"
)
# whole-word match so "Shelly's" is not "Shell"
CHAINS = re.compile(r"(?<![a-z])(?:%s)(?![a-z])" % _CHAIN_NAMES, re.I)

TYPE_POINTS = {
    "Barbershop": 10, "Hair salon": 9, "Beauty salon": 8, "Nail salon": 9, "Massage": 6, "Tattoo studio": 5,
    "Restaurant": 8, "Fast food / takeout": 6, "Cafe": 6, "Bakery": 6, "Food truck": 8, "Butcher / meat market": 5, "Deli": 5,
    "Auto repair": 8, "Tire shop": 5, "Car wash": 4,
    "Dry cleaner": 7, "Laundry / cleaner": 7,
    "Daycare": 6, "Pet grooming": 5, "Florist": 5, "Locksmith": 5,
    "Plumber": 5, "Electrician": 5, "HVAC": 5, "Carpenter": 5, "Painter": 5, "Roofer": 5, "Landscaping": 5,
}


def miles(lat, lon, center=CENTER):
    try:
        la1, lo1, la2, lo2 = map(math.radians, (float(lat), float(lon), center[0], center[1]))
    except (TypeError, ValueError):
        return None
    a = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 3958.8 * 2 * math.asin(math.sqrt(a))


def digits(s):
    return re.sub(r"\D", "", s or "")


def norm_name(name):
    # Same business spelled differently ("J & J", "JJ", "Zaza's"/"Zaza") gets the same key.
    n = re.split(r"\s+[-–@]\s+", name.lower())[0].replace("&", " and ")
    n = re.sub(r"['’]", "", n)
    words = [w for w in re.findall(r"[a-z0-9]+", n) if w not in ("the", "llc", "inc", "and")]
    return "".join(w[:-1] if len(w) > 3 and w.endswith("s") else w for w in words)


def single_row_reason(row):
    """Reason to drop a lead from its own data, or None."""
    name = row.get("name", "")
    if CLOSED.search(name):
        return "looks closed"
    if GOVERNMENT.search(name):
        return "school/government"
    if CHURCH.search(name):
        return "church (held out)"
    if CHAINS.search(name):
        return "big chain"
    return None


def clean(rows, blocked_ids=()):
    """Return (kept, removed) where removed is a list of (row, reason)."""
    removed, survivors = [], []
    for r in rows:
        reason = (blocked_ids.get(r["id"], "previously excluded") if isinstance(blocked_ids, dict) else "previously excluded") \
            if r["id"] in blocked_ids else single_row_reason(r)
        (removed.append((r, reason)) if reason else survivors.append(r))
    counts = {}
    for r in survivors:
        counts[norm_name(r["name"])] = counts.get(norm_name(r["name"]), 0) + 1
    kept, seen = [], []
    for r in survivors:
        key = norm_name(r["name"])
        if key and counts[key] >= 3:
            removed.append((r, "multi-location chain (3+ places)"))
            continue
        dup = next((k for k in seen if k[0] == key and (
            (digits(r.get("phone")) and digits(r.get("phone")) == k[1]) or
            (miles(r.get("lat"), r.get("lon"), (k[2], k[3])) or 9) < 0.08)), None)
        if dup:
            removed.append((r, "duplicate"))
            continue
        seen.append((key, digits(r.get("phone")), _f(r.get("lat")), _f(r.get("lon"))))
        kept.append(r)
    return kept, removed


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def score_parts(row, today=None):
    """(total, [human-readable reasons]) - higher is a better lead."""
    today = today or datetime.date.today()
    parts = []
    t = TYPE_POINTS.get(row.get("type"), 3)
    parts.append((t, "type %s" % row.get("type")))
    d = miles(row.get("lat"), row.get("lon"))
    if d is not None:
        parts.append((round(max(0.0, 12 * (1 - d / 10.0)), 1), "%.1f mi from 53218" % d))
    if row.get("phone"):
        parts.append((8, "has phone"))
    if row.get("hours"):
        parts.append((3, "hours listed"))
    try:
        age = (today - datetime.date.fromisoformat(row["updated"][:10])).days / 365.0
        if age <= 3:
            parts.append((2, "edited in last 3 yrs"))
        elif age > 7:
            parts.append((-2, "listing is old"))
    except (KeyError, ValueError, TypeError):
        pass
    if row.get("email") or row.get("social"):
        parts.append((1, "email/social listed"))
    return round(sum(p for p, _ in parts), 1), [r for _, r in parts]


def apply_scores(rows):
    for r in rows:
        d = miles(r.get("lat"), r.get("lon"))
        r["miles"] = "%.1f" % d if d is not None else ""
        r["score"] = score_parts(r)[0]
    return rows
