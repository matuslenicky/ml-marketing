// Stiahne písma z Google Fonts do assets/fonts a vypíše @font-face pravidlá (latin + latin-ext).
// Spustenie: node tools/fonts.mjs
import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const out = path.join(root, 'assets', 'fonts');
const CSS = 'https://fonts.googleapis.com/css2?family=Corben:wght@400;700&family=Albert+Sans:ital,wght@0,400..700;1,400..700&display=swap';
const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36';

await mkdir(out, { recursive: true });
const css = await (await fetch(CSS, { headers: { 'User-Agent': UA } })).text();
const blocks = [...css.matchAll(/\/\* ([\w-]+) \*\/\s*@font-face\s*\{([^}]+)\}/g)];
let local = '';
for (const [, subset, body] of blocks) {
  if (subset !== 'latin' && subset !== 'latin-ext') continue;
  const fam = /font-family:\s*'([^']+)'/.exec(body)[1];
  const style = /font-style:\s*(\w+)/.exec(body)[1];
  const url = /url\((https:[^)]+)\)/.exec(body)[1];
  // statické rezy (Corben 400 a 700) majú váhu v názve, variabilné písmo (rozsah váh) nie
  const weight = /font-weight:\s*([\d ]+)/.exec(body)[1].trim();
  const cut = weight.includes(' ') ? '' : `-${weight}`;
  const name = `${fam.toLowerCase().replace(/\s+/g, '-')}-${style}${cut}-${subset}.woff2`;
  const buf = Buffer.from(await (await fetch(url)).arrayBuffer());
  await writeFile(path.join(out, name), buf);
  local += `@font-face{${body.replace(/url\(https:[^)]+\)/, `url(${name})`).replace(/\s+/g, ' ').trim()}}\n`;
  console.log(name, buf.length);
}
await writeFile(path.join(out, 'fonts.css'), local);
console.log('subsets:', [...new Set(blocks.map(b => b[1]))].join(', '));
