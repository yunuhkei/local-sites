# Connect creamcitywebco.com (your own site) and clients' domains

## A. Your own domain: creamcitywebco.com
Your home page lives at the main page of this repo's GitHub Pages site. When you own a domain, the demos stay in their own folders under it (`creamcitywebco.com/<demo-name>/`).

1. **Buy the domain** (about $10-15 a year) at Cloudflare Registrar, Namecheap or Porkbun. Pay with your own account.
2. **Tell the site about it:** in `config.json` set `"custom_domain": "creamcitywebco.com"` (or ask Claude), then run `python3 sitemaker/build_home.py` and `python3 sitemaker/make_site.py` for each site, or just ask Claude to rebuild. This writes a `docs/CNAME` file and updates share links and the sitemap.
3. **DNS records** at the registrar (the DNS page):
   - Four **A** records for `@` (the bare domain): `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
   - One **CNAME** record: name `www`, value `yunuhkei.github.io`
4. In GitHub: repo **Settings > Pages > Custom domain**, type `creamcitywebco.com`, **Save**. Wait for the green check (minutes to a few hours).
5. Tick **Enforce HTTPS** when it appears.
6. Old `yunuhkei.github.io/local-sites/...` links redirect automatically.
7. Optional: free email like `hello@creamcitywebco.com` forwarding to your inbox (Cloudflare Email Routing or your registrar), then put it in `config.json` as `email`.

## B. A client's own domain (after they pay)
GitHub Pages allows **one custom domain per repository**, and yours is taken by Cream City Web Co. So each client who wants their own domain gets a tiny repo of their own:

1. The client **buys the domain in their own name** (you get DNS access).
2. Make the standalone folder: `python3 sitemaker/make_site.py sites/<client>/site.json --live --export out/<client> --cname www.clientdomain.com` (`--live` only after the owner approved and zero items are left in TO-GET-FROM-OWNER; it refuses otherwise).
3. New GitHub repo (like `client-barbershop`), upload the folder's files including `CNAME`. **Settings > Pages**: deploy from branch `main`, folder root.
4. DNS: same four **A** records for `@`, and a **CNAME** `www` pointing to `yunuhkei.github.io`. Tick **Enforce HTTPS**.
5. Delete the old demo folder from `docs/` so there aren't two copies.
