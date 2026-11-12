# Client agreement template (Cream City Web Co.)

**This is a template, not legal advice.** Fill in every `[bracket]`, pick the numbers you want, and have a free Wisconsin SBDC advisor, an accountant or an attorney read it once. Then reuse it for every client.

## How to use it
1. Fill in the brackets (one copy per client). Delete the bracket notes.
2. Send it **before** you build anything or take the deposit: as a text/email, a Google Doc link or a PDF.
3. The client replies **"I agree"** from their phone or email, or signs with a free e-signature tool (check each tool's free limits). Save a screenshot or the email.
4. Only then send the **$250 deposit link** (`guides/payments.md`).
5. Keep every signed copy in one folder, and mark the client in `data/clients.csv`.

**Privacy note:** the company is the party to this agreement, so no personal name is needed on the page. Send it from the business email (creamcitywebco@gmail.com) so the "from" is the company. Ask your advisor whether the company can accept as "Cream City Web Co." with a title like "Owner" (and, once you form an LLC, "Cream City Web Co., LLC"). A person's name may be needed only if a client or a court asks who signed.

---

# Website Agreement

**Between:** Cream City Web Co. ("we", "us") ([or "Cream City Web Co., LLC" once formed]), creamcitywebco@gmail.com, (414) 676-1916
**And:** [Client business name] ("you"), [contact name], [phone], [email]
**Date:** [date]

## 1. What we will build
A one-page website for [Business name] at [address], with your business name, services, hours, phone and map links, and the photos and words you give us. Add-ons: [none / list them].

## 2. Price and payments
- **Total price for the website: $500.**
- **$250 deposit**, due when you agree to this, before we build your final site.
- **$250 balance**, due within **[7] days after your site goes live**.
- **Hosting and small updates: $25 per month**, starting the day your site goes live.
- **Add-ons** (if any): [add-on, price, when due].
You pay using the secure payment links we send you.

## 3. How it works
We show you a free preview first. You tell us what to change, and we change it. **Nothing goes live until you say OK in writing (a text is fine).** Before it goes live, you confirm that the details on it are correct: hours, phone, address, services and prices.

## 4. What the $25 a month covers
Hosting, keeping your site online and secure, and small updates: changing hours, prices, phone, address or wording, and swapping photos. We aim to make requested updates within **[3] business days**. Extra pages are **$100 each**. Bigger changes (a redesign or an online store) are priced separately, and we tell you the price before we start.

## 5. Who owns what
- Your business name, logo, words and photos are yours.
- You promise you have the right to use everything you give us (photos, logos, text).
- We own the design and code of the website **until you have paid in full** ($500 plus any add-ons).
- **Once paid in full**, the finished site is yours to use for your business. While you are on the monthly plan, we host it. If you leave the plan, we will give you a copy of your site's files on request [within 14 days], as long as everything you owe has been paid.

## 6. Your domain name
If you buy a domain name (like yourshop.com), it is registered **in your name** and you own it. We never take control of your domain. Connecting it to your site is an add-on at the price listed in Section 2.

## 7. If a payment is late
If the balance or a monthly payment is more than **[7] days late**, we will remind you. If it is still unpaid after we send you **[7] days' written notice** (text or email), we may take your site offline until you pay. Taking the site offline is not a refund, and you still owe what is due.

## 8. Canceling
- You can cancel the monthly plan at any time by texting or emailing us. It ends at the end of that month, and we take your site offline then. If you have paid in full, we send you a copy of your files on request.
- If you cancel before your site goes live, **the deposit is not refundable**, because we have already done the work.
- If we are unable to finish your site, we refund the deposit.

## 9. No guarantees
We can't promise a number of customers, calls or any Google ranking. Your site is a tool to help people find and contact you.

## 10. Limits
To the extent the law allows, our total responsibility to you is limited to the amount you have paid us in the last 12 months, and we are not responsible for lost business or other indirect losses.

## 11. Privacy
We use the information you give us only to build and run your site. Anything you ask us to publish (phone, address, hours) will be public.

## 12. The whole agreement
This is our whole agreement. Changes must be in writing (a text is fine). Wisconsin law applies. If there's a problem, we agree to talk first and try to fix it.

## Agreed
**[Business name]**: by [client name] on [date]. ("I agree" by reply text or email counts.)
**Cream City Web Co.**: sent from creamcitywebco@gmail.com on [date].

---

# Short text version (to send with the full agreement)
> Hi [Name], here's the agreement for your website with Cream City Web Co.: [link]. In short: $500 total ($250 now, $250 within [7] days after it goes live), then $25 a month. Nothing goes live until you OK it, and you can cancel the monthly plan any time. Reply "I agree" and we'll send the deposit link. Thanks!

# Decisions you need to make once (then reuse)
- How many days for the balance after launch (I suggest **7**).
- How many days of notice before taking a site offline (I suggest **7**).
- Update turnaround (**3 business days** is realistic if you send changes to Claude the same day).
- Whether to give clients a copy of their files when they cancel (I recommend yes, once paid in full).

---

# The ready-to-send version (a link)
The same terms, with the default numbers filled in, are a page on your site: `/agreement/` (hidden from Google, not linked from the home page). Text it to every client, with your own message. Change the numbers in `config.json` under `terms` and pricing, then run `python3 sitemaker/build_home.py` to update the page and its version date.

Text to send:
> Hi [Name], here are the terms for your website with Cream City Web Co.: [your site address]/agreement/ . In short: $500 total ($250 to start, $250 within 7 days after it goes live), then $25 a month. Nothing goes live until you OK it, and you can cancel the monthly plan any time. Reply "I agree" and your business name, and we'll send the deposit link.
