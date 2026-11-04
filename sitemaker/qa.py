#!/usr/bin/env python3
"""Run every completeness check on published sites.

    python3 sitemaker/qa.py                      # all sites in docs/
    python3 sitemaker/qa.py docs/my-site --shots /tmp/shots
Static checks (files, SEO, schema, copy rules) + browser checks at 375/768/1280 px with screenshots.
"""
import argparse
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import checks  # noqa: E402


def static_checks(d, titles, descs):
    probs = []
    page = open(os.path.join(d, "index.html"), encoding="utf-8").read()
    live = 'name="robots"' not in page
    probs += checks.scan_page(page, live=live)
    for f in ("favicon.svg", "apple-touch-icon.png", "og.png", "404.html"):
        if not os.path.exists(os.path.join(d, f)):
            probs.append("missing file: " + f)
    og = os.path.join(d, "og.png")
    if os.path.exists(og) and os.path.getsize(og) > 150_000:
        probs.append("og.png is heavy (%d KB)" % (os.path.getsize(og) // 1024))
    for pat, label in ((r"<title>([^<]{10,70})</title>", "title"),
                       (r'<meta name="description" content="([^"]{30,200})"', "description")):
        m = re.search(pat, page)
        if not m:
            probs.append("missing or badly sized %s" % label)
        else:
            bucket = titles if label == "title" else descs
            if m.group(1) in bucket:
                probs.append("%s duplicates another site" % label)
            bucket.add(m.group(1))
    for tag in ('property="og:image"', 'property="og:title"', 'name="twitter:card"', 'rel="icon"', 'rel="apple-touch-icon"'):
        if tag not in page:
            probs.append("missing " + tag)
    m = re.search(r'<script type="application/ld\+json">(.*?)</script>', page, re.S)
    if not m:
        probs.append("no LocalBusiness JSON-LD")
    else:
        try:
            ld = json.loads(m.group(1))
            for k in ("name", "telephone", "address", "url", "image"):
                if not ld.get(k):
                    probs.append("JSON-LD missing %s" % k)
        except ValueError:
            probs.append("JSON-LD is not valid JSON")
    for img in re.findall(r'src="(photos/[^"]+)"', page):
        p = os.path.join(d, img)
        if not os.path.exists(p) or os.path.getsize(p) > 400_000:
            probs.append("photo missing or too heavy: " + img)
    if len(page.encode()) > 60_000:
        probs.append("index.html over 60 KB")
    return probs


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sites", nargs="*")
    ap.add_argument("--shots", default=os.path.join(ROOT, "qa-shots"))
    a = ap.parse_args()
    docs = os.path.join(ROOT, "docs")
    logged = [x["slug"] for x in checks.load_log(os.path.join(ROOT, "design-log.json"))["sites"]]
    sites = a.sites or [os.path.join(docs, n) for n in logged if os.path.exists(os.path.join(docs, n, "index.html"))]
    titles, descs, report = set(), set(), {}
    for s in sites:
        report[os.path.basename(s)] = static_checks(s, titles, descs)
    r = subprocess.run(["node", os.path.join(HERE, "qa_browser.js"), a.shots] + list(sites), capture_output=True, text=True)
    if r.returncode != 0:
        print("browser checks could not run:", r.stderr[-300:])
        return 2
    for slug, probs in json.loads(r.stdout.strip().splitlines()[-1]).items():
        report[slug] += probs
    bad = 0
    for slug, probs in report.items():
        print("%s  %s" % ("PASS" if not probs else "FAIL", slug))
        for p in probs:
            print("      - " + p)
        bad += bool(probs)
    print("Screenshots in", a.shots)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
