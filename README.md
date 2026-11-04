# local-sites

A tiny toolkit for a Milwaukee side business: find local businesses with no website, build them a demo site, show it on a phone, get paid.

| Folder | What it is |
|---|---|
| `leadfinder/find_leads.py` | Finds businesses with no website on OpenStreetMap -> `data/leads.csv` |
| `leadfinder/tracker.py` | Change a lead's status / see your pipeline |
| `leadfinder/notify.py` | Phone alert via ntfy (uses secret `ALERT_TARGET`) |
| `sitemaker/` | Site builder: brief check, design log, 2 layouts (poster, split), QA |
| `docs/` | What GitHub Pages publishes (demo sites + price sheet) |
| `pitch/` | Walk-in script and message templates |
| `guides/` | Setup, custom domains, payments, legal basics, daily plan |
| `.github/workflows/` | Weekly lead finder + "update status" button |

Start with `guides/setup-github.md`. Everything uses only Python 3 (nothing to install). Run tests: `python3 -m unittest discover -s tests`.

## Making a website (design rules are in `CLAUDE.md` and enforced by code)
```
python3 sitemaker/make_site.py --scaffold <lead-id>     # starter brief + site.json for a lead
# write sites/<slug>/brief.md, fill sites/<slug>/site.json (Claude does this from your intake notes)
python3 sitemaker/make_site.py sites/<slug>/site.json   # builds docs/<slug>/ ; refuses if a rule is broken
python3 sitemaker/qa.py                                 # browser checks + screenshots at 375/768/1280
```
Each build updates `design-log.json` and writes `sites/<slug>/TO-GET-FROM-OWNER.md`. Two sample designs are included (`corner-chair-barbershop`, `60th-street-auto-repair`, both pretend businesses).

## Other commands
```
python3 leadfinder/find_leads.py          # find leads (needs internet)
python3 leadfinder/tracker.py summary
python3 -m unittest discover -s tests
```
Lead data: (c) OpenStreetMap contributors, ODbL. Demo sites are labeled previews and hidden from search engines until `--live` with the owner's OK.
