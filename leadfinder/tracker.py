#!/usr/bin/env python3
"""Update lead statuses and see your pipeline.

    python3 leadfinder/tracker.py summary
    python3 leadfinder/tracker.py set osm-node-123 contacted --note "left card, call Tue"
    python3 leadfinder/tracker.py list new
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import find_leads  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", default="data/leads.csv")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("summary")
    p = sub.add_parser("list"); p.add_argument("status", choices=find_leads.STATUSES)
    p = sub.add_parser("set"); p.add_argument("lead_id"); p.add_argument("status", choices=find_leads.STATUSES)
    p.add_argument("--note", default="")
    a = ap.parse_args(argv)
    rows = find_leads.load_csv(a.csv)

    if a.cmd == "summary":
        for s in find_leads.STATUSES:
            print("%-15s %d" % (s, sum(1 for r in rows if r["status"] == s)))
        print("%-15s %d" % ("TOTAL", len(rows)))
    elif a.cmd == "list":
        for r in rows:
            if r["status"] == a.status:
                print("%s | %s | %s | %s" % (r["id"], r["name"], r["type"], r["phone"]))
    else:
        for r in rows:
            if r["id"] == a.lead_id:
                r["status"] = a.status
                if a.note:
                    r["notes"] = (r["notes"] + " / " if r["notes"] else "") + a.note.replace("\n", " ")
                find_leads.save_csv(a.csv, rows)
                print("Updated %s -> %s" % (r["name"], a.status))
                return 0
        print("No lead with id %s" % a.lead_id, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
