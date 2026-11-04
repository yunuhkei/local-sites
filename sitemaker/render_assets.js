// Renders og.png (1200x630, for text-message link previews) and apple-touch-icon.png (180x180).
// Usage: node render_assets.js <build_dir with og.html + icon.html> <out_dir>
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const [buildDir, outDir] = process.argv.slice(2);
  const browser = await chromium.launch();
  const jobs = [['og.html', 'og.png', 1200, 630], ['icon.html', 'apple-touch-icon.png', 180, 180]];
  for (const [src, dest, w, h] of jobs) {
    const page = await browser.newPage({ viewport: { width: w, height: h } });
    await page.goto('file://' + path.resolve(buildDir, src));
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(300);
    await page.screenshot({ path: path.resolve(outDir, dest) });
    await page.close();
  }
  await browser.close();
})().catch(e => { console.error(String(e)); process.exit(1); });
