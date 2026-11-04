# Connecting a custom domain (~$12/year, paid by the client)

GitHub Pages allows **one custom domain per repository**. So after a client pays, give their site its own tiny repo:

1. **Buy the domain in the client's name** (Cloudflare Registrar, Namecheap, or Porkbun, about $10-15/year). The client owns it; you get DNS access.
2. **Make the standalone site folder:**
   `python3 sitemaker/make_site.py --config sites/<client>.json --live --export out/<client> --cname www.clientdomain.com`
   (`--live` only after the owner approved the site.)
3. **New GitHub repo** (e.g. `client-barbershop`), upload the files in `out/<client>` (including `CNAME`). Settings -> Pages -> Deploy from branch `main` / root.
4. **DNS records at the registrar:**
   - `www`  **CNAME** -> `<your-github-name>.github.io`
   - Root/apex `@` **A** records -> `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
5. Wait (minutes to a few hours). In Settings -> Pages, tick **Enforce HTTPS** when it's available.
6. Remove the old demo folder from `local-sites/docs/` so there aren't two copies.
