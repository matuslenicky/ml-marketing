# ML&T Marketing

Firemný web: weby pre služby, ktoré žijú z rezervácií a objednávok (výber miesta, termínu alebo opravy), s 3D scénou z Blendera podľa fotiek priestoru.

Živá verzia: https://matuslenicky.github.io/ml-marketing/

## Stav

Pracovná verzia. Stránka má `noindex`, kontakty sú zástupné (`data-contact`) a formulár nič neodosiela na server, len otvorí e-mail návštevníka s vyplnenou správou.

## Ukážky v `ukazky/`

Vymyslené prevádzky, rezervácie sa ukladajú len do `localStorage` prehliadača. Každá ukážka má hore pás, že ide o ukážku, a `noindex`.

- `ukazky/restauracia/` – Bistro Kôrka: sála z Blendera, hosť zvolí deň, čas a počet osôb a vyberie si konkrétny stôl. Scéna: `blender/scena.py`, spúšťa `blender/render.sh`; polohy stolov v `assets/stoly.json` sú vypočítané v Blenderi.
- `ukazky/autoservis/` – RAMPA 7: predrenderovaná sekvencia dielne (`assets/seq/`) prehrávaná pri skrolovaní, body služieb na aute (`blender/body.json` z Blendera), cenník, objednávka termínu a `admin.html` s prehľadom rezervácií. Model auta `blender/auto.py` používa generátor zo susedného projektu `parcela`.

Blender skripty berú zámok `.blender.lock` v koreni repozitára, aby naraz nebežali dva Blendery.

## Ako je to postavené

- `index.html` je celá hlavná stránka, bez buildu. Farby v pomere približne 50 % biela, 40 % kobaltová modrá, 10 % limetkový akcent, len svetlý režim.
- `data-pack` na tlačidlách cenníka sa musí zhodovať s `<option>` vo formulári.
- `assets/fonts`: Wix Madefor Display a Text (SIL OFL), `node tools/fonts.mjs`.
- `assets/img`: zábery prác. `node tools/shots.mjs <dir>` a `node tools/shots-extra.mjs <dir>` (živé weby), `node tools/shots-demos.mjs <dir>` (ukážky v `ukazky/`), prevod na WebP cez `python tools/prep.py`, `prep-extra.py`, `prep-demos.py`.
- `node tools/view.mjs <out.png> <selector> [šírka]` urobí záber časti stránky na kontrolu.
