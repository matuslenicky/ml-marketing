// Skúška na mobile: výber balíka v úvode, tlačidlo balíka, prázdne a vyplnené odoslanie formulára.
// mailto sa zachytí, nič sa neodošle. Spustenie: node tools/form-test.mjs <out.png>
import { createRequire } from 'node:module';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const require = createRequire(path.join(process.env.APPDATA, 'npm', 'node_modules', 'x.js'));
const { chromium } = require('playwright');
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, hasTouch: true, isMobile: true });
const page = await ctx.newPage();
let mailto = null;
page.on('request', r => { if (r.url().startsWith('mailto:')) mailto = r.url(); });
await page.goto(pathToFileURL(path.join(root, 'index.html')).href, { waitUntil: 'load' });

// Výber balíka v úvode: každá záložka a každý balík musí nájsť svoju voľbu vo formulári.
const options = await page.locator('#f-pack option').allTextContents();
let bad = 0, seen = 0;
for (const tab of await page.locator('.calc-tab').all()) {
  await tab.click();
  const n = await page.locator('#calc-list input').count();
  for (let i = 0; i < n; i++) {
    await page.locator('#calc-list .calc-opt').nth(i).click();
    const want = await page.locator('#calc-go').getAttribute('data-pack');
    const price = (await page.locator('#calc-sum-price').textContent()).replace(/ /g, ' ');
    seen++;
    if (!options.includes(want)) { bad++; console.log('CHÝBA vo formulári:', want); }
    else console.log('ok', want, '|', price, '|', (await page.locator('#calc-sum-more').textContent()).replace(/ /g, ' '));
  }
}
console.log('kombinácií:', seen, 'chýb:', bad);

await page.locator('#calc-go').click();
await page.waitForTimeout(600);
console.log('z úvodu predvyplnené:', await page.locator('#f-pack').inputValue());

await page.locator('#kluby [data-pack="Kluby – Klubový web s redakciou"]').click();
await page.waitForTimeout(600);
console.log('z karty predvyplnené:', await page.locator('#f-pack').inputValue());

await page.locator('#form button[type=submit]').click();
console.log('chyba:', await page.locator('#form-note').textContent());
console.log('aria-invalid meno/kontakt:', await page.locator('#f-name').getAttribute('aria-invalid'), await page.locator('#f-reach').getAttribute('aria-invalid'));
await page.locator('#form').screenshot({ path: process.argv[2] });

await page.fill('#f-name', 'Skúšobný Človek');
await page.fill('#f-reach', '0900 000 000');
await page.locator('#form button[type=submit]').click();
await page.waitForTimeout(300);
console.log('po odoslaní:', await page.locator('#form-note').textContent());
console.log('mailto:', mailto ? decodeURIComponent(mailto).slice(0, 150).replace(/\n/g, ' / ') : 'nezachytený');
await browser.close();
