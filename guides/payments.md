# Getting paid (simplest way)

## Option A - Stripe Payment Link (recommended)
1. Make a free account at stripe.com and finish verification (do this yourself; never share keys with anyone or paste them in code or chat).
2. Dashboard -> **Payment Links** -> **Create**.
3. Add two products: **Website setup** $250 (one-time) and **Hosting & updates** $25 (recurring monthly). One link can bill both: setup today, then $25 each month.
4. Copy the link (it looks like `buy.stripe.com/...`) and text it to the client **after they approve the site**.
5. Stripe emails receipts and shows who paid under **Payments** and **Subscriptions** (failed payments are flagged there).

## Option B - Square Invoices
Square app -> Invoices -> create an invoice with a **recurring** schedule. Good if the client already uses Square.

## Option C - Cash/Zelle/check
OK for the $250 setup; give a receipt. For the monthly part, a recurring invoice or payment link is easier than chasing.

## Tracking who paid
- When money arrives, set the lead's status to **paid** (GitHub app -> Actions -> "Update a lead's status" -> Run workflow, or edit `data/leads.csv`).
- Add the client to `data/clients.csv` (domain, start month, last month paid). Stripe's Subscriptions page is the source of truth.
- Once a month: check Stripe for failed/late payments and follow up politely. Pause or take down the site only after a clear notice.
