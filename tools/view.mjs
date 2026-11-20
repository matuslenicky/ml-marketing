// Záber časti stránky: node tools/view.mjs <out.png> <selector> [šírka=1280] [dark]
import { createRequire } from 'node:module';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const require = createRequire(path.join(process.env.APPDATA, 'npm', 'node_modules', 'x.js'));
const { chromium } = require('playwright');
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const [out, sel, w = '1280', mode] = process.argv.slice(2);
const phone = Number(w) < 600;

const browser = await chromium.launch();
const ctx = await browser.newContext({
  viewport: { width: Number(w), height: phone ? 844 : 900 },
  deviceScaleFactor: phone ? 2 : 1,
  colorScheme: mode === 'dark' ? 'dark' : 'light',
});
const page = await ctx.newPage();
await page.goto(pathToFileURL(path.join(root, 'index.html')).href, { waitUntil: 'load' });
await page.evaluate(async () => {
  for (let y = 0; y < document.body.scrollHeight; y += 600) { scrollTo(0, y); await new Promise(r => setTimeout(r, 60)); }
  const shown = [...document.images].filter(i => i.offsetParent !== null && !i.complete);
  await Promise.race([
    Promise.all(shown.map(i => new Promise(r => { i.onload = i.onerror = r; }))),
    new Promise(r => setTimeout(r, 4000)),
  ]);
  await document.fonts.ready;
});
const el = page.locator(sel).first();
await el.scrollIntoViewIfNeeded();
await page.waitForTimeout(200);
await el.screenshot({ path: out });
await browser.close();
