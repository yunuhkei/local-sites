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
          else if (!/^(#|tel:|sms:|mailto:|https:\/\/|\.\/|[a-z0-9][a-z0-9._\/-]*)/.test(h) || /^(http:|javascript:)/.test(h)) out.problems.push('odd link: ' + h); });
        document.querySelectorAll('img').forEach(i => { if (!i.complete || i.naturalWidth === 0) out.problems.push('image failed: ' + i.src); });
        // real rendered contrast (WCAG AA) for every piece of text
        const parse = c => { let m = c.match(/rgba?\(([^)]+)\)/); if (m) { const p = m[1].split(/[ ,\/]+/).filter(Boolean).map(Number); return [p[0], p[1], p[2], p.length > 3 ? p[3] : 1]; }
          m = c.match(/color\(srgb ([^)]+)\)/); if (m) { const p = m[1].split(/[ \/]+/).filter(Boolean).map(Number); return [p[0]*255, p[1]*255, p[2]*255, p.length > 3 ? p[3] : 1]; } return [0,0,0,1]; };
        const lum = ([r,g,b]) => { const f = v => { v/=255; return v <= .03928 ? v/12.92 : Math.pow((v+.055)/1.055, 2.4); }; return .2126*f(r)+.7152*f(g)+.0722*f(b); };
        const bgOf = el => { let layers = []; for (let n = el; n; n = n.parentElement) { const s = getComputedStyle(n); if (s.backgroundImage !== 'none' && !/^url/.test(s.backgroundImage)) return null; const c = parse(s.backgroundColor); if (c[3] > 0) layers.push(c); if (c[3] >= 1) break; }
          let base = [255,255,255]; for (let i = layers.length - 1; i >= 0; i--) { const [r,g,b,a] = layers[i]; base = [r*a+base[0]*(1-a), g*a+base[1]*(1-a), b*a+base[2]*(1-a)]; } return base; };
        const seen = new Set();
        document.querySelectorAll('h1,h2,h3,p,li,td,th,dt,dd,a,address,summary,label,span,button,.banner').forEach(el => {
          const own = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()); if (!own) return;
          const st = getComputedStyle(el); if (st.display === 'none' || st.visibility === 'hidden') return;
          const r = el.getBoundingClientRect(); if (r.width === 0 || r.height === 0) return;
          const bg = bgOf(el); if (!bg) return; const fg = parse(st.color); let op = 1; for (let n = el; n; n = n.parentElement) op *= parseFloat(getComputedStyle(n).opacity); const a = fg[3] * op;
          const f = [fg[0]*a+bg[0]*(1-a), fg[1]*a+bg[1]*(1-a), fg[2]*a+bg[2]*(1-a)];
          const L1 = lum(f), L2 = lum(bg), ratio = (Math.max(L1,L2)+.05)/(Math.min(L1,L2)+.05);
          const size = parseFloat(st.fontSize), bold = parseInt(st.fontWeight) >= 700; const large = size >= 24 || (size >= 18.66 && bold);
          const need = large ? 3 : 4.5;
          if (ratio < need - 0.01) { const t = el.textContent.trim().slice(0, 28); if (!seen.has(t)) { seen.add(t); out.problems.push('low contrast ' + ratio.toFixed(1) + ':1 (needs ' + need + '): "' + t + '"'); } }
        });
        return out;
      });
      r.problems.forEach(p => problems.push(vname + ': ' + p));
      errors.forEach(e => problems.push(vname + ': ' + e));
      await page.screenshot({ path: path.join(outDir, slug + '-' + vname + '-fold.png') });
      await page.evaluate(async () => { for (let y = 0; y < document.body.scrollHeight; y += 500) { window.scrollTo({ top: y, behavior: 'instant' }); await new Promise(r => setTimeout(r, 70)); } window.scrollTo({ top: 0, behavior: 'instant' }); });
      await page.waitForTimeout(300);
      if (vname !== 'small-phone') await page.screenshot({ path: path.join(outDir, slug + '-' + vname + '-full.png'), fullPage: true });
      await ctx.close();
    }
    // the footer must not be hidden behind the sticky bottom bar when scrolled to the end
    { const c2 = await browser.newContext({ viewport: { width: 375, height: 812 }, isMobile: true, hasTouch: true }); const pg = await c2.newPage();
      await pg.goto('file://' + path.resolve(dir, 'index.html')); await pg.evaluate(() => window.scrollTo({ top: document.body.scrollHeight, behavior: 'instant' })); await pg.waitForTimeout(200);
      const covered = await pg.evaluate(() => { const f = document.querySelector('.foot, footer'); if (!f) return false; const bar = document.querySelector('.callbar'); if (!bar || getComputedStyle(bar).display === 'none') return false;
        return f.getBoundingClientRect().bottom > bar.getBoundingClientRect().top + 1; });
      if (covered) problems.push('footer is hidden behind the sticky bottom bar at the end of the page');
      await c2.close(); }
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
