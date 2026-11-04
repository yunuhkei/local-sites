# One-time setup (all doable from your phone's browser)

## 1. The repository
You already have `yunuhkei/local-sites`. (If you ever need a new one: github.com -> **+** -> New repository -> name `local-sites` -> **Public** (free Pages needs public) -> Create.)

## 2. Get the code onto the main branch
The work lives on branch `claude/milwaukee-local-sites-builder-cqwxkr`. Open a pull request into `main` and **Merge** it (or ask Claude to open it). Weekly Actions and Pages both run from `main`.

## 3. Turn on GitHub Pages
Repo -> **Settings** -> **Pages** -> *Build and deployment* -> Source: **Deploy from a branch** -> Branch: `main`, folder: **/docs** -> **Save**. After ~1 minute your demo is at:
`https://yunuhkei.github.io/local-sites/demo-barbershop/`

## 4. Phone alerts
1. Install the free **ntfy** app, subscribe to a long random topic name (it acts like a password).
2. Repo -> **Settings** -> **Secrets and variables** -> **Actions** -> **New repository secret** -> Name `ALERT_TARGET`, Value = your topic. (Type it in GitHub only.)
3. Repo -> **Actions** -> "Weekly lead finder" -> **Run workflow** to test now.
4. Also allow the bot to save: Settings -> Actions -> General -> Workflow permissions -> **Read and write**.

## Privacy note
Free Pages requires a public repo, so `data/leads.csv` is public. It's only public OpenStreetMap data plus your status/notes - keep notes polite and minimal, or use a private repo (needs a paid GitHub plan for Pages).
