# local-sites

A tiny toolkit for a Milwaukee side business: find local businesses with no website, build them a demo site, show it on a phone, get paid.

| Folder | What it is |
|---|---|
| `leadfinder/find_leads.py` | Finds businesses with no website on OpenStreetMap -> `data/leads.csv` |
| `leadfinder/tracker.py` | Change a lead's status / see your pipeline |
| `leadfinder/notify.py` | Phone alert via ntfy (uses secret `ALERT_TARGET`) |
| `sitemaker/make_site.py` | Builds a one-page site (4 templates: barber, salon, food, service) |
| `docs/` | What GitHub Pages publishes (demo sites + price sheet) |
| `pitch/` | Walk-in script and message templates |
| `guides/` | Setup, custom domains, payments, legal basics, daily plan |
| `.github/workflows/` | Weekly lead finder + "update status" button |

Start with `guides/setup-github.md`. Everything uses only Python 3 (nothing to install). Run tests: `python3 -m unittest discover -s tests`.

## Commands
```
python3 leadfinder/find_leads.py                      # find leads (needs internet)
python3 sitemaker/make_site.py --lead <id>            # demo site for a lead -> docs/<name>-<code>/
python3 sitemaker/make_site.py --config sites/demo-barbershop.json
python3 leadfinder/tracker.py summary
```
Optional per-lead edits: create `sites/<name>-<code>.json` (copy `sites/demo-barbershop.json`) and drop photos in a folder `sites/<name>-<code>/`.

Lead data: (c) OpenStreetMap contributors, ODbL. Demo sites are labeled previews and hidden from search engines until you run with `--live` with the owner's OK.
