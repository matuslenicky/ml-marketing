// Skúška formulára na mobile: prázdne odoslanie (chyba) a vyplnené odoslanie (zachytený mailto, nič sa neodošle).
// Spustenie: node tools/form-test.mjs <out.png>
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
await page.route(u => u.protocol === 'mailto:', r => { mailto = r.request().url(); r.abort(); });
page.on('request', r => { if (r.url().startsWith('mailto:')) mailto = r.url(); });
await page.goto(pathToFileURL(path.join(root, 'index.html')).href, { waitUntil: 'load' });

await page.locator('[data-pack="Kluby – Klubový web s redakciou"]').click();
await page.waitForTimeout(700);
console.log('predvyplnené:', await page.locator('#f-pack').inputValue());

await page.locator('#form button[type=submit]').click();
console.log('chyba:', await page.locator('#form-note').textContent());
console.log('aria-invalid meno/kontakt:', await page.locator('#f-name').getAttribute('aria-invalid'), await page.locator('#f-reach').getAttribute('aria-invalid'));
console.log('fokus:', await page.evaluate(() => document.activeElement.id));
await page.locator('#form').screenshot({ path: process.argv[2] });

await page.fill('#f-name', 'Skúšobný Človek');
await page.fill('#f-reach', '0900 000 000');
await page.locator('#form button[type=submit]').click();
await page.waitForTimeout(300);
console.log('po odoslaní:', await page.locator('#form-note').textContent());
console.log('trieda chyby:', await page.locator('#form-note').getAttribute('class'));
console.log('mailto:', mailto ? decodeURIComponent(mailto).slice(0, 160) : 'nezachytený');
await browser.close();
