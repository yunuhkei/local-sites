// Browser checks at phone / small phone / tablet / desktop sizes. Prints JSON.
// Usage: node qa_browser.js <screenshot_out_dir> <site_dir> [<site_dir> ...]
const { chromium } = require('playwright');
const path = require('path'), fs = require('fs');
const VIEWS = [['phone', 375, 812], ['small-phone', 375, 667], ['tablet', 768, 1024], ['desktop', 1280, 800]];
(async () => {
  const [outDir, ...sites] = process.argv.slice(2);
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch();
  const report = {};
  for (const dir of sites) {
    const slug = path.basename(dir), problems = [];
    for (const [vname, w, h] of VIEWS) {
      const ctx = await browser.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: vname === 'desktop' ? 1 : 2, isMobile: w < 800, hasTouch: w < 800 });
      const page = await ctx.newPage();
      const errors = [];
      page.on('pageerror', e => errors.push('JS error: ' + e.message));
      page.on('console', m => { if (m.type() === 'error') errors.push('console: ' + m.text()); });
      page.on('requestfailed', r => errors.push('request failed: ' + r.url()));
      await page.goto('file://' + path.resolve(dir, 'index.html'));
      await page.evaluate(() => document.fonts.ready);
      await page.waitForTimeout(300);
      const r = await page.evaluate(() => {
        const out = { problems: [] };
        const sw = document.documentElement.scrollWidth - window.innerWidth;
        if (sw > 0) out.problems.push('sideways scroll: ' + sw + 'px');
        const tel = [...document.querySelectorAll('a[href^="tel:"]')].filter(a => {
          const b = a.getBoundingClientRect(); const s = getComputedStyle(a);
          return s.display !== 'none' && b.width > 0 && b.top >= 0 && b.bottom <= window.innerHeight; });
        if (!tel.length) out.problems.push('no visible tap-to-call button without scrolling');
        document.querySelectorAll('.btn, .callbar a').forEach(a => {
          const b = a.getBoundingClientRect(), s = getComputedStyle(a);
          if (s.display !== 'none' && b.height > 0 && b.height < 44) out.problems.push('tap target too small: ' + a.textContent.trim() + ' (' + Math.round(b.height) + 'px)'); });
        document.querySelectorAll('p,li,td,th,dt,dd,a,address').forEach(el => {
          if (el.closest('.banner') || !el.textContent.trim()) return;
          const s = getComputedStyle(el); if (s.display === 'none') return;
          if (parseFloat(s.fontSize) < 13) out.problems.push('text under 13px: ' + el.textContent.trim().slice(0, 30)); });
        document.querySelectorAll('a[href]').forEach(a => {
          const h = a.getAttribute('href');
          if (h === '#' || h === '') out.problems.push('empty link');
          else if (h.startsWith('#') && !document.getElementById(h.slice(1))) out.problems.push('broken anchor ' + h);
          else if (!/^(#|tel:|sms:|mailto:|https:\/\/|\.\/)/.test(h)) out.problems.push('odd link: ' + h); });
        document.querySelectorAll('img').forEach(i => { if (!i.complete || i.naturalWidth === 0) out.problems.push('image failed: ' + i.src); });
        return out;
      });
      r.problems.forEach(p => problems.push(vname + ': ' + p));
      errors.forEach(e => problems.push(vname + ': ' + e));
      await page.screenshot({ path: path.join(outDir, slug + '-' + vname + '-fold.png') });
      if (vname !== 'small-phone') await page.screenshot({ path: path.join(outDir, slug + '-' + vname + '-full.png'), fullPage: true });
      await ctx.close();
    }
    // keyboard: Tab should land on visible focus within the page
    const ctx = await browser.newContext({ viewport: { width: 375, height: 812 } });
    const page = await ctx.newPage(); await page.goto('file://' + path.resolve(dir, 'index.html'));
    await page.keyboard.press('Tab'); await page.keyboard.press('Tab');
    const ok = await page.evaluate(() => document.activeElement && document.activeElement !== document.body);
    if (!ok) problems.push('keyboard: Tab does not reach links');
    await ctx.close();
    report[slug] = problems;
  }
  await browser.close();
  console.log(JSON.stringify(report));
})().catch(e => { console.error(String(e)); process.exit(1); });
