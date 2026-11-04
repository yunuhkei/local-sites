#!/usr/bin/env python3
"""Make the "Top 20 this week" list from data/leads.csv (status = new).

    python3 leadfinder/rank.py              # writes data/top20.md and prints it
    python3 leadfinder/rank.py --top 30
Score = type + distance from ZIP 53218 + has phone + hours listed + recently edited (see leadqa.py).
"""
import argparse
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import find_leads  # noqa: E402
import leadqa  # noqa: E402


def google(q):
    return "https://www.google.com/search?q=" + urllib.parse.quote(q)


def load_review(path="data/review.csv"):
    return {r["id"]: r for r in find_leads.load_csv(path)}


def build(rows, top, skip_ids=(), review=None):
    review = review if review is not None else load_review()
    cand = [r for r in rows if r["status"] == "new" and r["id"] not in skip_ids
            and review.get(r["id"], {}).get("verdict") != "exclude"]
    for r in cand:
        r["_score"], r["_why"] = leadqa.score_parts(r)
        v = review.get(r["id"], {}).get("verdict", "")
        r["_score"] += {"confirmed": 4, "unverified": -4}.get(v, 0)
        r["_check"] = {"confirmed": "Checked: found online, no website", "unverified": "NOT VERIFIED - check first"}.get(v, "Not checked yet")
    cand.sort(key=lambda r: -r["_score"])
    out = ["# Top %d this week\n" % top,
           "Ranked by: closest to 53218, best business types, has a phone, hours listed, recently edited. "
           "**Before you visit, tap the Google link** - 'no website in OpenStreetMap' is not proof they have none.\n",
           "| # | Business | Type | Miles | Phone | Address | Score | Status | Check |", "|---|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(cand[:top], 1):
        q = "%s %s" % (r["name"], (r["address"].split(",")[-2:-1] or ["Milwaukee"])[0].strip() if r["address"] else "Milwaukee WI")
        out.append("| %d | %s | %s | %s | %s | %s | %.1f | %s | [Google](%s) |" % (
            i, r["name"], r["type"], r["miles"], r["phone"] or "-", r["address"] or "-", r["_score"], r["_check"], google(q)))
    return "\n".join(out) + "\n", cand[:top]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", default="data/leads.csv")
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--out", default="data/top20.md")
    a = ap.parse_args(argv)
    text, _ = build(find_leads.load_csv(a.csv), a.top)
    open(a.out, "w", encoding="utf-8").write(text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
