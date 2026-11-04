#!/usr/bin/env python3
"""Send a phone alert through ntfy. The topic comes from the ALERT_TARGET environment
variable (a GitHub secret) - it is never written in code and never printed.

    ALERT_TARGET=mytopic python3 leadfinder/notify.py "3 new businesses without a website near you"

ALERT_TARGET may be a bare topic name (sent to https://ntfy.sh/<topic>) or a full URL
if you run your own ntfy server.
"""
import os
import sys
import urllib.request


def target_url(raw):
    raw = (raw or "").strip()
    if not raw:
        return None
    return raw if raw.startswith("https://") else "https://ntfy.sh/" + raw.lstrip("/")


def main(argv):
    url = target_url(os.environ.get("ALERT_TARGET"))
    if not url:
        print("ALERT_TARGET is not set - skipping phone alert.")
        return 0
    message = argv[1] if len(argv) > 1 else "Lead finder finished."
    headers = {"Title": "Local Sites", "Tags": "briefcase", "User-Agent": "local-sites-notify/1.0"}
    click = os.environ.get("ALERT_CLICK_URL")
    if click:
        headers["Click"] = click
    req = urllib.request.Request(url, data=message.encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print("Phone alert sent (HTTP %s)." % r.status)
    except Exception as e:  # never print the URL: it contains the secret topic
        print("Phone alert failed: %s" % type(e).__name__)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
