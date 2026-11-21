// Náhľady vlastných ukážok (ukazky/restauracia, ukazky/autoservis) pre hlavnú stránku.
// Spustenie: node tools/shots-demos.mjs <outDir>   potom: python tools/prep-demos.py <outDir>
import { createRequire } from 'node:module';
import { mkdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const require = createRequire(path.join(process.env.APPDATA, 'npm', 'node_modules', 'x.js'));
const { chromium } = require('playwright');
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const out = process.argv[2];
await mkdir(out, { recursive: true });
const url = p => pathToFileURL(path.join(root, 'ukazky', p, 'index.html')).href;

const browser = await chromium.launch();
async function ctx(phone) {
  return browser.newContext(phone
    ? { viewport: { width: 390, height: 780 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true }
    : { viewport: { width: 1280, height: 800 }, deviceScaleFactor: 1 });
}

// Reštaurácia: sála s vyznačenými stolmi.
for (const phone of [false, true]) {
  const c = await ctx(phone);
  const page = await c.newPage();
  await page.goto(url('restauracia'), { waitUntil: 'load' });
  await page.waitForTimeout(800);
  // Sála na stred okna, aby boli vidno stoly s vyznačením voľných a obsadených.
  await page.evaluate(() => {
    const img = document.querySelector('img[src*="sala"]');
    const r = img.getBoundingClientRect();
    scrollTo(0, r.top + scrollY - Math.max(0, (innerHeight - r.height) / 2) - (innerWidth < 600 ? 40 : 0));
  });
  await page.waitForTimeout(900);
  await page.screenshot({ path: path.join(out, phone ? 'm-restauracia.png' : 'demo-restauracia.png') });
  await c.close();
}

// Autoservis: koniec 3D sekvencie s bodmi služieb.
for (const phone of [false, true]) {
  const c = await ctx(phone);
  const page = await c.newPage();
  await page.goto(url('autoservis'), { waitUntil: 'load' });
  await page.waitForTimeout(1200);
  for (let i = 0; i < 30; i++) {
    await page.mouse.wheel(0, phone ? 220 : 260);
    await page.waitForTimeout(140);
    const n = await page.locator('.spots button').evaluateAll(els => els.filter(e => {
      const r = e.getBoundingClientRect(); const s = getComputedStyle(e);
      return r.width > 0 && r.top >= 0 && r.bottom <= innerHeight && Number(s.opacity) > 0.5;
    }).length).catch(() => 0);
    if (n >= 5) break;
  }
  await page.waitForTimeout(600);
  await page.screenshot({ path: path.join(out, phone ? 'm-autoservis.png' : 'demo-autoservis.png') });
  await c.close();
}
await browser.close();
console.log('hotovo');
