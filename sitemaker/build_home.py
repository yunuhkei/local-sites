#!/usr/bin/env python3
"""Build the Cream City Web Co. home page, price sheet, 404, sitemap and robots into docs/.

    python3 sitemaker/build_home.py            # reads config.json (contact details, pricing, FAQ)
Until phone, email, form link and payment link are filled in, the page is a DRAFT: it shows
labeled TO GET FROM OWNER items and is hidden from Google. Once they're all there it goes public.
"""
import html
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import checks  # noqa: E402

PALETTE = {"bg": "#EADFC4", "ink": "#2B2118", "muted": "#5C4C3C", "accent": "#1B5560", "on_accent": "#F8F1DE",
           "panel": "#2B2118", "on_panel": "#EADFC4"}
FONTS = {"head": "Young Serif", "body": "Public Sans", "head_weight": 400,
         "url_params": "family=Young+Serif&family=Public+Sans:wght@400;600;700",
         "head_fallback": "Georgia, serif", "body_fallback": "system-ui, sans-serif"}
TRADES = ["Barbers", "Hair salons", "Nail shops", "Restaurants", "Food trucks", "Auto shops", "Cleaners", "Daycares"]
DESIGN = {"layout": "studio-onepager", "fonts": FONTS, "palette": PALETTE,
          "hero": "left-aligned headline over a Cream City brick course",
          "section_order": ["hero", "how", "samples", "pricing", "preview", "faq", "about", "area"],
          "signature": "running-bond Cream City brick course"}


def esc(s):
    return html.escape(str(s), quote=True)


def digits(p):
    d = re.sub(r"\D", "", p or "")
    return "1" + d if len(d) == 10 else d


def todo(what):
    return '<span class="todo">TO GET FROM OWNER: %s</span>' % esc(what)


def load():
    c = json.load(open(os.environ.get("CONFIG_PATH") or os.path.join(ROOT, "config.json"), encoding="utf-8"))
    c["base"] = ("https://" + c["custom_domain"].strip()) if c.get("custom_domain") else c["pages_base"].rstrip("/")
    return c


def css():
    pal = "".join("--%s:%s;" % (k, v) for k, v in PALETTE.items())
    root = ":root{%s--head-font:'%s',%s;--body-font:'%s',%s}\n" % (pal, FONTS["head"], FONTS["head_fallback"], FONTS["body"], FONTS["body_fallback"])
    return root + open(os.path.join(HERE, "home", "home.css"), encoding="utf-8").read()


FONT_URL = "https://fonts.googleapis.com/css2?%s&display=swap" % FONTS["url_params"]


def head(c, title, desc, extra="", live=True, path=""):
    robots = "" if live else '<meta name="robots" content="noindex,nofollow">'
    canon = '<link rel="canonical" href="%s/%s">' % (esc(c["base"]), path) if live else ""
    og = "\n".join('<meta %s="%s" content="%s">' % (a, k, esc(v)) for a, k, v in [
        ("property", "og:type", "website"), ("property", "og:site_name", c["brand"]), ("property", "og:title", title),
        ("property", "og:description", desc), ("property", "og:url", "%s/%s" % (c["base"], path)),
        ("property", "og:image", c["base"] + "/og.png"), ("property", "og:image:width", "1200"),
        ("property", "og:image:height", "630"), ("name", "twitter:card", "summary_large_image")])
    up = "../" if path else ""
    return ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">\n'
            '<title>%s</title>\n<meta name="description" content="%s">\n%s\n%s\n<meta name="theme-color" content="%s">\n%s\n'
            '<link rel="icon" href="%sfavicon.svg" type="image/svg+xml"><link rel="apple-touch-icon" href="%sapple-touch-icon.png">\n'
            '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
            '<link rel="stylesheet" href="%s" media="print" onload="this.media=\'all\'"><noscript><link rel="stylesheet" href="%s"></noscript>\n'
            '<style>\n%s</style>\n%s</head>' % (esc(title), esc(desc), robots, canon, PALETTE["panel"], og, up, up, FONT_URL, FONT_URL, css(), extra))


def home(c, live):
    ph, em = c.get("phone", ""), c.get("email", "")
    d = digits(ph)
    tel, sms = ("tel:+" + d, "sms:+" + d) if d else (None, None)
    who = (c.get("contact_name") or "").strip()      # optional first name; blank = company voice
    title = "Websites for Milwaukee small businesses | %s" % c["brand"]
    desc = "%s builds simple, mobile-friendly websites for Milwaukee small businesses. Free preview first, then $%d to build and $%d a month." % (c["brand"], c["pricing"]["setup"], c["pricing"]["monthly"])
    ld = {"@context": "https://schema.org", "@type": "ProfessionalService", "name": c["brand"], "url": c["base"] + "/",
          "image": c["base"] + "/og.png", "description": desc,
          "areaServed": [{"@type": "City", "name": t} for t in c["service_area"]],
          "address": {"@type": "PostalAddress", "addressLocality": "Milwaukee", "addressRegion": "WI", "addressCountry": "US"},
          "priceRange": "$%d to build + $%d per month" % (c["pricing"]["setup"], c["pricing"]["monthly"])}
    if d:
        ld["telephone"] = "+" + d
    if em:
        ld["email"] = em
    extra = '<script type="application/ld+json">%s</script>\n' % json.dumps(ld).replace("</", "<\\/")
    pr = c["pricing"]

    about_text = ("I'm %s. I live in Milwaukee and I build websites for the shops and services around here. When you call or text, you get me, not a call center." % esc(who)) if who else \
        "%s is a local Milwaukee business. We build websites for the shops and services around here. When you call or text, you reach a real person here, not a call center." % esc(c["brand"])
    phone_line = ('Prefer to talk? Call or text %s: <a href="%s">%s</a>' % (esc(who or "us"), tel, esc(ph))) if tel else todo("phone number")
    top_phone = ('<a class="top-phone" href="%s">%s</a>' % (tel, esc(ph))) if tel else ""
    banner = "" if live else '<div class="banner">DRAFT · not public yet, still missing contact details</div>'

    addons = "".join('<li><b><span style="color:inherit;font-size:inherit">%s</span><span style="color:inherit;font-size:inherit">$%d</span></b><span>%s</span></li>'
                     % (esc(a["name"]), a["price"], esc(a["note"])) for a in pr["addons"])
    faq = "".join("<details><summary>%s</summary><p>%s</p></details>" % (esc(q), esc(a)) for q, a in c["faq"])
    towns = "".join("<li>%s</li>" % esc(t) for t in c["service_area"])
    pay = ('<a class="btn" href="%s">Pay to get started</a>' % esc(c["stripe_link"])) if c.get("stripe_link") else todo("Stripe Payment Link")
    fid = c.get("formspree_id")
    action = "https://formspree.io/f/%s" % esc(fid) if fid else ""
    form_note = "" if fid else '<p>%s</p>' % todo("Formspree form link (the form can't send until it's added)")
    email_line = ('<a class="btn line" href="mailto:%s">Email %s</a>' % (esc(em), esc(who or "us"))) if em else todo("email address")
    contact_btns = ('<a class="btn" href="%s">Call %s</a><a class="btn line" href="%s">Send a text</a>' % (tel, esc(ph), sms)) if tel else todo("phone number")
    callbar = ('<a href="%s">Call</a><a href="%s">Text</a><a href="#preview">Free preview</a>' % (tel, sms)) if tel else '<a href="#preview">Get your free preview</a>'

    def sample(slug, img, alt, label):
        return ('<figure><a href="%s/"><img src="assets/%s" width="360" height="780" alt="%s" loading="lazy" decoding="async"></a>'
                '<figcaption><a href="%s/">%s</a><br>Made for a pretend business.</figcaption></figure>' % (slug, img, esc(alt), slug, esc(label)))
    samples = sample("corner-chair-barbershop", "sample-barbershop.jpg",
                     "Phone screen of a sample barbershop website: big red and black type reading Corner Chair, a Call button and a ticket-shaped hours box.",
                     "Sample: barbershop") + \
        sample("60th-street-auto-repair", "sample-auto-repair.jpg",
               "Phone screen of a sample auto repair website: dark panel, bold condensed type reading 60th Street Auto Repair and a yellow Call button.",
               "Sample: auto repair")

    body = f'''<body>
<a class="skip" href="#main">Skip to content</a>
{banner}
<header class="top"><a class="brand" href="./">{esc(c["brand"])}</a><span class="top-right">{top_phone}<a class="btn small" href="#preview">Free preview</a></span></header>
<main id="main">
<section class="hero"><div class="wrap">
<div>
<p class="kicker">Milwaukee · small business websites</p>
<h1>Websites for Milwaukee small businesses, ready in a week.</h1>
<p class="lede">You get a free preview first. Nothing to pay until you say yes.</p>
<a class="btn" href="#preview">Get your free preview</a>
<p class="sub">{phone_line}</p>
</div>
<aside class="made-for" aria-labelledby="mf"><h2 id="mf">Made for</h2><ul>{"".join("<li>%s</li>" % t for t in TRADES)}<li>and other local shops</li></ul></aside>
</div></section>
<div class="bricks" aria-hidden="true"></div>

<section class="sec" id="how"><div class="wrap"><h2>How it works</h2>
<ol class="steps">
<li><h3>We make a free preview</h3><p>Tell us about your business. We build a real preview of your website on your phone, using your name, your phone number and your address.</p></li>
<li><h3>You check it out</h3><p>Open the link. Tell us what to change: hours, words, photos, colors. We fix it.</p></li>
<li><h3>It goes live when you're happy</h3><p>Say yes and it goes live. Not before.</p></li>
</ol>
<p class="note">Nothing to pay until you say yes.</p></div></section>

<section class="sec dark" id="samples"><div class="wrap"><h2>Sample work</h2>
<p>These are samples for pretend businesses, so you can see how a site looks and works on a phone. Yours gets its own colors, words and photos, based on your shop's sign and storefront.</p>
<div class="phones">{samples}</div></div></section>

<section class="sec" id="pricing"><div class="wrap"><h2>Pricing, plain</h2>
<div class="board">
<div class="row"><span class="price">${pr["setup"]}</span><span class="what">to build your site, paid in two parts: ${pr["deposit"]} to get started and ${pr["balance"]} when it goes live</span></div>
<div class="row"><span class="price">${pr["monthly"]}</span><span class="what">a month, to keep it online and updated (starts when it goes live)</span></div>
</div>
<ul class="incl"><li>A website that works great on a phone</li><li>One page is included. Extra pages are ${pr["extra_page"]} each</li><li>Tap to call, tap for directions, your hours, your services</li><li>Hosting and security included</li><li>Small updates included: new hours, prices and photos</li><li>Cancel any time</li></ul>
<h3 style="margin-top:28px;font-size:1.5rem">Add-ons, if you want them</h3>
<ul class="addons">{addons}</ul>
<p class="fineprint">A domain name (like yourshop.com) costs about $12 a year, paid by you to the domain company. It's registered in your name.</p>
<div class="pay"><p><b>Already said yes?</b> Pay your ${pr["deposit"]} deposit to get started. Please wait until you've seen your preview. The other ${pr["balance"]} is due when your site goes live.</p>{pay}</div>
</div></section>

<section class="sec dark" id="preview"><div class="wrap"><h2>Get your free preview</h2>
<p>Fill this in and {esc(who) + ' will' if who else 'we will'} contact you. It's free, and there's nothing to pay unless you say yes.</p>
{form_note}
<form id="signup" action="{action}" method="POST">
<label>Business name<input name="business_name" required autocomplete="organization"></label>
<label>Your name<input name="owner_name" required autocomplete="name"></label>
<label>Phone number<input name="phone" type="tel" required autocomplete="tel"></label>
<label>What does your business do?<input name="what_they_do" required placeholder="Example: barbershop, nail salon, auto repair"></label>
<label>Do you have a website now?<select name="has_website" required><option value="">Choose one</option><option>No website</option><option>Only a Facebook or Instagram page</option><option>Yes, but I want a new one</option></select></label>
<p class="hp" aria-hidden="true"><label>Leave this empty<input name="_gotcha" tabindex="-1" autocomplete="off"></label></p>
<input type="hidden" name="_subject" value="New free preview request: Cream City Web Co.">
<button class="btn" type="submit">Send me my free preview</button>
<p class="msg" id="msg" role="status" aria-live="polite"></p>
</form></div></section>

<section class="sec" id="faq"><div class="wrap"><h2>Questions</h2>{faq}</div></section>

<section class="sec alt" id="about"><div class="wrap"><h2>About</h2>
<p style="max-width:56ch">{about_text}</p>
<p>{phone_line}</p><div class="contact-row">{contact_btns}{email_line}</div></div></section>

<section class="sec" id="area"><div class="wrap"><h2>Where we work</h2>
<p style="max-width:56ch">Milwaukee and the suburbs around it, including:</p><ul class="towns">{towns}</ul></div></section>
</main>
<div class="bricks" aria-hidden="true"></div>
<footer class="foot"><p>&copy; 2026 {esc(c["brand"])} · Milwaukee, WI</p><p><a href="price-sheet/">Printable price sheet</a></p></footer>
<nav class="callbar" aria-label="Quick contact">{callbar}</nav>
<script>
(function(){{var f=document.getElementById('signup');if(!f||!f.action||f.action===location.href)return;
f.addEventListener('submit',function(e){{e.preventDefault();var m=document.getElementById('msg');m.textContent='Sending...';
fetch(f.action,{{method:'POST',body:new FormData(f),headers:{{'Accept':'application/json'}}}}).then(function(r){{
if(r.ok){{f.reset();m.textContent='Thanks! {esc(who) + ' will' if who else 'We will'} contact you soon.';}}else{{m.textContent='Something went wrong. Please call or text instead.';}}
}}).catch(function(){{m.textContent='Something went wrong. Please call or text instead.';}});}});}})();
</script>
</body></html>'''
    return head(c, title, desc, extra, live) + "\n" + body


def price_sheet(c):
    pr = c["pricing"]
    ph, em = c.get("phone", ""), c.get("email", "")
    d = digits(ph)
    contact = " · ".join([('<a href="tel:+%s">%s</a>' % (d, esc(ph))) if d else todo("phone number"),
                              ('<a href="mailto:%s">%s</a>' % (esc(em), esc(em))) if em else todo("email address")])
    addons = "".join("<tr><td>%s<span>%s</span></td><td>$%d</td></tr>" % (esc(a["name"]), esc(a["note"]), a["price"]) for a in pr["addons"])
    title, desc = "Website pricing | %s" % c["brand"], "Simple pricing from %s: $%d to build and $%d a month for a Milwaukee small business website, plus optional add-ons." % (c["brand"], pr["setup"], pr["monthly"])
    extra = "<style>.ps{max-width:720px;margin:0 auto;padding:28px 20px}.ps table{width:100%;border-collapse:collapse;margin-top:8px}.ps td{padding:12px 0;border-bottom:1px dotted var(--muted)}.ps td:last-child{text-align:right;font-weight:700;white-space:nowrap;vertical-align:top}.ps td span{display:block;color:var(--muted);font-size:.95rem}.ps .board{margin:20px 0}</style>\n"
    return head(c, title, desc, extra, live=False, path="price-sheet/") + f'''
<body><a class="skip" href="#main">Skip to content</a>
<main id="main" class="ps"><p class="kicker">{esc(c["brand"])} · Milwaukee</p>
<h1 style="font-size:clamp(2rem,8vw,3rem)">Website pricing</h1>
<div class="board"><div class="row"><span class="price">${pr["setup"]}</span><span class="what">to build your site, paid in two parts: ${pr["deposit"]} to get started and ${pr["balance"]} when it goes live</span></div>
<div class="row"><span class="price">${pr["monthly"]}</span><span class="what">a month, to keep it online and updated (starts when it goes live)</span></div></div>
<ul class="incl"><li>A website that works great on a phone</li><li>One page is included. Extra pages are ${pr["extra_page"]} each</li><li>Tap to call, tap for directions, your hours, your services</li><li>Free preview first. You pay nothing until you say yes</li><li>Pay in two parts: ${pr["deposit"]} to start, ${pr["balance"]} when it goes live</li><li>Hosting, security and small updates included</li><li>Cancel any time. Your domain name is registered in your name</li></ul>
<h2 style="font-size:1.6rem;margin-top:28px">Add-ons</h2><table><tbody>{addons}</tbody></table>
<p class="fineprint">A domain name costs about $12 a year, paid by you to the domain company.</p>
<p style="margin-top:26px;border-top:3px solid var(--ink);padding-top:14px"><b>{esc(c["brand"])}</b>, Milwaukee<br>{contact}</p>
</main></body></html>'''


def agreement_page(c):
    """Client-facing terms page. Not linked from the home page and hidden from Google; text the link to a client."""
    pr, t = c["pricing"], c["terms"]
    ph, em = c.get("phone", ""), c.get("email", "")
    d = digits(ph)
    addons = "".join("<li>%s: $%d</li>" % (esc(a["name"]), a["price"]) for a in pr["addons"])
    contact = " · ".join([("<a href=\"tel:+%s\">%s</a>" % (d, esc(ph))) if d else todo("phone number"),
                              ("<a href=\"mailto:%s\">%s</a>" % (esc(em), esc(em))) if em else todo("email address")])
    title = "Website agreement | %s" % c["brand"]
    desc = "The terms for a website built by %s: price, payments, what is included, ownership and cancelling." % c["brand"]
    extra = "<style>.agr{max-width:720px;margin:0 auto;padding:28px 20px 60px}.agr h2{font-size:1.5rem;margin:30px 0 8px}.agr p,.agr li{max-width:62ch}.agr ul{padding-left:1.2rem}.agr .ver{color:var(--muted);font-size:.95rem}.agr .agree{border:3px solid var(--ink);padding:16px 20px;margin-top:30px}</style>\n"
    body = f"""<body><a class="skip" href="#main">Skip to content</a>
<main id="main" class="agr"><p class="kicker">{esc(c["brand"])} · Milwaukee</p>
<h1 style="font-size:clamp(2rem,8vw,3rem)">Website agreement</h1>
<p class="ver">Version: {esc(t["version"])}</p>
<p>This agreement is between <b>{esc(c["brand"])}</b> ("we") and the business that agrees to it below ("you"). It is short and in plain words.</p>

<h2>1. What we will build</h2>
<p>A one-page website for your business, with your business name, services, hours, phone and map links, and the photos and words you give us. Any add-ons you want are listed in the message we send you with this page.</p>

<h2>2. Price and payments</h2>
<ul>
<li><b>Total price for the website: ${pr["setup"]}.</b></li>
<li><b>${pr["deposit"]} deposit</b>, due when you agree to this, before we build your final site.</li>
<li><b>${pr["balance"]} balance</b>, due within <b>{t["balance_days"]} days after your site goes live</b>.</li>
<li><b>Hosting and small updates: ${pr["monthly"]} a month</b>, starting the day your site goes live.</li>
<li>Add-ons, only if you ask for them:<ul>{addons}</ul></li>
</ul>
<p>You pay using the secure payment links we send you.</p>

<h2>3. How it works</h2>
<p>We show you a free preview first. You tell us what to change, and we change it. <b>Nothing goes live until you say OK in writing (a text is fine).</b> Before it goes live, you confirm that the details on it are correct: hours, phone, address, services and prices.</p>

<h2>4. What the ${pr["monthly"]} a month covers</h2>
<p>Hosting, keeping your site online and secure, and small updates: changing hours, prices, phone, address or wording, and swapping photos. We aim to make requested updates within {esc(t["turnaround"])}. Extra pages are ${pr["extra_page"]} each. Bigger changes (a redesign or an online store) are priced separately, and we tell you the price before we start.</p>

<h2>5. Who owns what</h2>
<ul>
<li>Your business name, logo, words and photos are yours.</li>
<li>You promise you have the right to use everything you give us (photos, logos, text).</li>
<li>We own the design and code of the website <b>until you have paid in full</b> (${pr["setup"]} plus any add-ons).</li>
<li><b>Once paid in full</b>, the finished site is yours to use for your business. While you are on the monthly plan, we host it. If you leave the plan, we will give you a copy of your site's files on request within {t["files_days"]} days, as long as everything you owe has been paid.</li>
</ul>

<h2>6. Your domain name</h2>
<p>If you buy a domain name (like yourshop.com), it is registered <b>in your name</b> and you own it. We never take control of your domain. Connecting it to your site is an add-on at the price in Section 2.</p>

<h2>7. If a payment is late</h2>
<p>If the balance or a monthly payment is more than {t["balance_days"]} days late, we will remind you. If it is still unpaid after we send you {t["notice_days"]} days' written notice (text or email), we may take your site offline until you pay. Taking the site offline is not a refund, and you still owe what is due.</p>

<h2>8. Cancelling</h2>
<ul>
<li>You can cancel the monthly plan at any time by texting or emailing us. It ends at the end of that month, and we take your site offline then. If you have paid in full, we send you a copy of your files on request.</li>
<li>If you cancel before your site goes live, the deposit is not refundable, because we have already done the work.</li>
<li>If we are unable to finish your site, we refund the deposit.</li>
</ul>

<h2>9. No guarantees</h2>
<p>We cannot promise a number of customers, calls or any Google ranking. Your site is a tool to help people find and contact you.</p>

<h2>10. Limits</h2>
<p>To the extent the law allows, our total responsibility to you is limited to the amount you have paid us in the last 12 months, and we are not responsible for lost business or other indirect losses.</p>

<h2>11. Privacy</h2>
<p>We use the information you give us only to build and run your site. Anything you ask us to publish (phone, address, hours) will be public.</p>

<h2>12. The whole agreement</h2>
<p>This is our whole agreement. Changes must be in writing (a text is fine). Wisconsin law applies. If there is a problem, we agree to talk first and try to fix it.</p>

<div class="agree"><h2 style="margin-top:0">How you agree</h2>
<p>Reply to our text or email with <b>"I agree"</b> and your <b>business name</b>. The date of your reply is the date of the agreement. This page, version {esc(t["version"])}, is the agreement. Questions first? {contact}</p></div>
</main><footer class="foot"><p>&copy; 2026 {esc(c["brand"])} · Milwaukee, WI</p></footer></body></html>"""
    return head(c, title, desc, extra, live=False, path="agreement/") + "\n" + body


def page_404(c):
    return head(c, "Page not found | %s" % c["brand"], "That page isn't here. Go back to the %s home page." % c["brand"], "", live=False) + \
        '<body><main id="main" class="wrap" style="padding-top:60px"><h1>Page not found</h1><p>That page isn\'t here.</p><a class="btn" href="./">Back to %s</a></main></body></html>' % esc(c["brand"])


def assets(c, out):
    p = PALETTE
    og = ('<!doctype html><meta charset="utf-8"><link rel="stylesheet" href="%s"><style>html,body{margin:0}body{width:1200px;height:630px;background:%s;color:%s;font-family:"Public Sans",sans-serif;position:relative;overflow:hidden}'
          '.b{position:absolute;left:0;right:0;bottom:0;height:120px;background-color:#E2D5B6;background-image:url("data:image/svg+xml,%%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'160\' height=\'80\'%%3E%%3Cpath d=\'M0 2h160M0 42h160M2 0v40M82 0v40M42 40v40M122 40v40\' stroke=\'%%232B2118\' stroke-opacity=\'.38\' stroke-width=\'4\' fill=\'none\'/%%3E%%3C/svg%%3E")}'
          '.k{position:absolute;left:80px;top:64px;font:700 28px "Public Sans";letter-spacing:.14em;text-transform:uppercase;color:%s}'
          'h1{position:absolute;left:80px;right:80px;top:110px;margin:0;font:400 104px/1.02 "Young Serif",Georgia,serif}'
          '.s{position:absolute;left:80px;top:372px;font:600 38px/1.3 "Public Sans";max-width:900px}</style>'
          '<div class="k">Milwaukee · small business websites</div><h1>%s</h1><div class="s">Websites ready in a week. Free preview first.</div><div class="b"></div>'
          % (FONT_URL, p["bg"], p["ink"], p["muted"], esc(c["brand"])))
    icon = ('<!doctype html><meta charset="utf-8"><link rel="stylesheet" href="%s"><style>html,body{margin:0}body{width:180px;height:180px;background:%s;color:%s;display:flex;align-items:center;justify-content:center;font:400 84px "Young Serif",Georgia,serif}</style>CC'
            % (FONT_URL, p["accent"], p["on_accent"]))
    b = os.path.join(ROOT, "sites", "cream-city-web-co", "_build")
    os.makedirs(b, exist_ok=True)
    open(os.path.join(b, "og.html"), "w", encoding="utf-8").write(og)
    open(os.path.join(b, "icon.html"), "w", encoding="utf-8").write(icon)
    r = subprocess.run(["node", os.path.join(HERE, "render_assets.js"), b, out], capture_output=True, text=True)
    if r.returncode:
        print("WARNING: share image not rendered:", r.stderr[-300:], file=sys.stderr)
    open(os.path.join(out, "favicon.svg"), "w").write(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="12" fill="%s"/><text x="32" y="43" text-anchor="middle" font-family="Georgia,serif" font-weight="700" font-size="30" fill="%s">CC</text></svg>'
        % (p["accent"], p["on_accent"]))


def main():
    out = os.path.join(ROOT, "docs") if len(sys.argv) < 2 else sys.argv[1]
    c = load()
    missing = [k for k in ("phone", "email", "formspree_id", "stripe_link") if not c.get(k)]
    live = not missing
    errs = checks.check_palette(PALETTE) + checks.check_brief(os.path.join(ROOT, "sites", "cream-city-web-co", "brief.md"))
    if errs:
        sys.exit("Cannot build:\n  - " + "\n  - ".join(errs))
    page = home(c, live)
    errs = checks.scan_page(page, live=live)
    if errs:
        sys.exit("Home page failed the design rules:\n  - " + "\n  - ".join(errs))
    os.makedirs(os.path.join(out, "price-sheet"), exist_ok=True)
    open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(page)
    open(os.path.join(out, "price-sheet", "index.html"), "w", encoding="utf-8").write(price_sheet(c))
    os.makedirs(os.path.join(out, "agreement"), exist_ok=True)
    open(os.path.join(out, "agreement", "index.html"), "w", encoding="utf-8").write(agreement_page(c))
    open(os.path.join(out, "404.html"), "w", encoding="utf-8").write(page_404(c))
    open(os.path.join(out, "sitemap.xml"), "w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>%s/</loc></url></urlset>\n' % c["base"])
    open(os.path.join(out, "robots.txt"), "w").write("User-agent: *\nAllow: /\nSitemap: %s/sitemap.xml\n" % c["base"])
    if c.get("custom_domain"):
        open(os.path.join(out, "CNAME"), "w").write(c["custom_domain"].strip() + "\n")
        open(os.path.join(out, ".nojekyll"), "w").close()
    assets(c, out)
    entry = checks.design_entry({"slug": "cream-city-web-co", "name": c["brand"], "design": dict(DESIGN)}, DESIGN["section_order"])
    logp = os.path.join(ROOT, "design-log.json")
    log = checks.load_log(logp)
    bad = checks.design_conflicts(entry, log["sites"])
    if bad:
        sys.exit("Design too similar to: %s" % bad)
    checks.save_log(logp, log, entry)
    print("Built %s home page -> %s" % ("PUBLIC" if live else "DRAFT (noindex)", out))
    if missing:
        print("Still needed in config.json: " + ", ".join(missing))


if __name__ == "__main__":
    main()
