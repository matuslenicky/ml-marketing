// Zábery hotových prác na ukážky (desktop 1280 × 800). Spustenie: node tools/shots.mjs <outDir>
import { createRequire } from 'node:module';
import { mkdir } from 'node:fs/promises';
import path from 'node:path';

const require = createRequire(path.join(process.env.APPDATA, 'npm', 'node_modules', 'x.js'));
const { chromium } = require('playwright');

const outDir = process.argv[2];
const SHOTS = [
  ['parcela', 'https://matuslenicky.github.io/parcela/'],
  ['klub-kovarce', 'https://matuslenicky.github.io/ofk-kovarce/'],
  ['klub-krajne', 'https://matuslenicky.github.io/tj-slovan-rovnost-krajne/'],
  ['klub-melcice', 'https://matuslenicky.github.io/fk-melcice-lieskove/'],
  ['hlbina', 'https://matuslenicky.github.io/hlbina/'],
];

await mkdir(outDir, { recursive: true });
const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 }, deviceScaleFactor: 1, colorScheme: 'light' });
for (const [name, url] of SHOTS) {
  const page = await ctx.newPage();
  try {
    const res = await page.goto(url, { waitUntil: 'networkidle', timeout: 45000 });
    await page.waitForTimeout(1200);
    await page.screenshot({ path: path.join(outDir, name + '.png') });
    console.log(name, res && res.status());
  } catch (e) {
    console.log(name, 'CHYBA', e.message.split('\n')[0]);
  }
  await page.close();
}
await browser.close();
