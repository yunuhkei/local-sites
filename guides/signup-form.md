# Make the "Get your free preview" form email you (Formspree, free)

The form on the home page sends new sign-ups to your email. Nothing secret goes in the page; the form link is public.

1. Go to **formspree.io** and sign up (free plan: 50 sign-ups a month).
2. Tap **New Form**. Name it "Cream City Web Co." and enter the email where you want sign-ups.
3. Formspree shows a form endpoint like `https://formspree.io/f/abcdwxyz`. The last part (`abcdwxyz`) is your **form ID**.
4. **Spam protection:** the page already has a hidden honeypot field Formspree reads. In the form's **Settings**, also turn on **reCAPTCHA** (free) if you see spam.
5. Send that form ID to Claude (it is not a secret) or put it in `config.json` as `formspree_id`, then run `python3 sitemaker/build_home.py`.
6. Test: submit the form once yourself and check your email (and the spam folder). Confirm Formspree's "confirm your email" message first.

Never put a password, API key, or your ntfy topic into the page or `config.json`.
