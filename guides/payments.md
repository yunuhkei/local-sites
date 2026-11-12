# Getting paid: Stripe Payment Link (simplest)

Your home page has a **Pay to get started** button. You create the link; it's public, not secret.

## The payment plan
- **$500 per site**, split in two: **$250 deposit** when they say yes to their preview, and **$250** when the site goes live.
- **$25 a month** for hosting and small updates, starting when the site goes live.

## Create two links (once)
1. Make a free account at **stripe.com** and finish verification yourself. Never share keys or passwords with anyone, in chat or in code.
2. In the Stripe Dashboard go to **Payment Links** > **Create**.
3. **Link 1, "Website deposit":** one product, $250, one time. This is the link for your website's **Pay to get started** button.
4. **Link 2, "Launch payment":** two items in one link: **Website balance**, $250 one time, and **Hosting & updates**, $25 recurring monthly. When a client pays it at launch they pay $275 once, and then $25 a month. If you'd rather charge the first month later, make the balance and the monthly plan two separate links.
5. Copy each link (they look like `https://buy.stripe.com/xxxxxxxx`).
6. Put Link 1 in `config.json` as `stripe_link` (or send it to Claude), then run `python3 sitemaker/build_home.py`. Keep Link 2 handy to text to a client the day their site goes live.

## When to send what
1. They see their preview and say yes, in writing (a text is fine): send **Link 1** (deposit).
2. You build and polish their real site with them.
3. They give the OK, the site goes live: send **Link 2** the same day.
4. Never send either link before they've said yes. The button on your site says "Already said yes?" on purpose.

## Protect yourself: a short written OK
Because the second $250 comes after the site is live, get a text or email from the client that says something like: "I agree to a $500 website from Cream City Web Co.: $250 now and $250 when it goes live, then $25 a month. I can cancel the monthly plan any time. Cream City Web Co. can take the site down if the balance isn't paid within 14 days of launch." Save a screenshot. This isn't legal advice, but it makes the terms clear for everyone. Pick the number of days you're comfortable with.

The full one-page agreement is in **`guides/client-agreement.md`**: fill in the brackets, send it before you build anything, get an "I agree" reply, then send the deposit link.

## Add-ons
Make extra Payment Links for add-ons (extra page $100 each, Google Business Profile $75, logo $75, domain connection $25) and text them when a client says yes. Prices come from `config.json`.

## Track who paid
- Stripe's **Payments** and **Subscriptions** pages are the source of truth (failed monthly payments show up there).
- Set the lead's status to **paid** (GitHub Actions > "Update a lead's status" > Run workflow).
- Add the client to `data/clients.csv`: domain, start month, last month paid.
- Once a month: check Stripe for failed or late payments and follow up politely.

## Alternatives
Square Invoices with a recurring schedule works too. Cash or Zelle is fine for the deposit and balance; give a receipt.
