// Doplnkové zábery: živá mapa z webu Parcela (desktop aj telefón) a klubový web na telefóne.
// Spustenie: node tools/shots-extra.mjs <outDir>
import { createRequire } from 'node:module';
import { mkdir } from 'node:fs/promises';
import path from 'node:path';

const require = createRequire(path.join(process.env.APPDATA, 'npm', 'node_modules', 'x.js'));
const { chromium } = require('playwright');
const outDir = process.argv[2];
await mkdir(outDir, { recursive: true });

const browser = await chromium.launch();
async function shot(name, url, vp, selector, phone) {
  const ctx = await browser.newContext({ viewport: vp, deviceScaleFactor: phone ? 2 : 1, isMobile: !!phone, hasTouch: !!phone, colorScheme: 'light' });
  const page = await ctx.newPage();
  try {
    await page.goto(url, { waitUntil: 'networkidle', timeout: 45000 });
    await page.waitForTimeout(1200);
    if (selector) {
      const el = page.locator(selector).first();
      await el.scrollIntoViewIfNeeded();
      await page.waitForTimeout(500);
      await el.screenshot({ path: path.join(outDir, name + '.png') });
    } else {
      await page.screenshot({ path: path.join(outDir, name + '.png') });
    }
    console.log(name, 'ok');
  } catch (e) {
    console.log(name, 'CHYBA', e.message.split('\n')[0]);
  }
  await ctx.close();
}

await shot('parcela-mapa', 'https://matuslenicky.github.io/parcela/', { width: 1280, height: 900 }, '.demo');
await shot('m-parcela', 'https://matuslenicky.github.io/parcela/', { width: 390, height: 780 }, null, true);
await shot('m-klub', 'https://matuslenicky.github.io/tj-slovan-rovnost-krajne/', { width: 390, height: 780 }, null, true);
await shot('m-hlbina', 'https://matuslenicky.github.io/hlbina/', { width: 390, height: 780 }, null, true);
await browser.close();
