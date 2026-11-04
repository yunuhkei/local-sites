"""Turn simple OpenStreetMap opening_hours text into [["Monday","10:00-19:00"], ...].

Only handles plain weekly schedules ("Mo-Fr 09:00-17:00; Sa 10:00-14:00; Su off").
Anything fancier (holidays, sunrise, two shifts a day, overnight) returns None, so we
never guess. Days OpenStreetMap doesn't mention are shown as Closed (its convention).
"""
import re

DAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _days(spec):
    out = set()
    for part in spec.split(","):
        part = part.strip()
        m = re.fullmatch(r"(Mo|Tu|We|Th|Fr|Sa|Su)(?:\s*-\s*(Mo|Tu|We|Th|Fr|Sa|Su))?", part)
        if not m:
            return None
        a = DAYS.index(m.group(1))
        b = DAYS.index(m.group(2)) if m.group(2) else a
        out.update(range(a, b + 1) if a <= b else list(range(a, 7)) + list(range(0, b + 1)))
    return out


def parse(text):
    if not text or re.search(r"PH|sunrise|sunset|week|\[|\+|\"|24/7|open|\bby\b", text):
        return None
    result = {}
    for rule in [r.strip() for r in text.split(";") if r.strip()]:
        m = re.fullmatch(r"([A-Za-z,\- ]+?)\s+(off|closed|\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2})", rule)
        if not m:
            return None
        days = _days(m.group(1))
        if days is None:
            return None
        spec = m.group(2)
        if spec in ("off", "closed"):
            val = "Closed"
        else:
            a, b = (x.strip() for x in spec.split("-"))
            if b <= a:                      # overnight - don't guess
                return None
            val = "%02d:%s-%02d:%s" % (int(a.split(":")[0]), a.split(":")[1], int(b.split(":")[0]), b.split(":")[1])
        for d in days:
            result[d] = val
    if not result:
        return None
    return [[NAMES[i], result.get(i, "Closed")] for i in range(7)]
