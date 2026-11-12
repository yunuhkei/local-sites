# Getting paid: Stripe Payment Link (simplest)

Your home page has a **Pay to get started** button. You create the link; it's public, not secret.

## Create the link (once)
1. Make a free account at **stripe.com** and finish verification yourself. Never share keys or passwords with anyone, in chat or in code.
2. In the Stripe Dashboard go to **Payment Links** > **Create**.
3. Add two products: **Website setup**, $250, one time. **Hosting & updates**, $25, recurring monthly. One link can bill both (setup today, then $25 each month).
4. Create the link. It looks like `https://buy.stripe.com/xxxxxxxx`. Copy it.
5. Put it in `config.json` as `stripe_link` (or send it to Claude), then run `python3 sitemaker/build_home.py`. Test it with Stripe's test mode first if you like.

## Add-ons
Make extra Payment Links for add-ons (Google Business Profile $75, booking or menu page $100, logo $75, domain connection $25) and text them when a client says yes. Prices come from `config.json`.

## When to send it
Only after the client has seen the preview and said yes. Never before. The button says "Already said yes?" on purpose.

## Track who paid
- Stripe's **Payments** and **Subscriptions** pages are the source of truth (failed monthly payments show up there).
- Set the lead's status to **paid** (GitHub Actions > "Update a lead's status" > Run workflow).
- Add the client to `data/clients.csv`: domain, start month, last month paid.
- Once a month: check Stripe for failed or late payments and follow up politely.

## Alternatives
Square Invoices with a recurring schedule works too. Cash or Zelle is fine for the $250 setup; give a receipt.
