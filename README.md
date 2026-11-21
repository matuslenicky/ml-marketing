# ML&T Marketing

Firemný web: weby pre služby, ktoré žijú z rezervácií a objednávok (výber miesta, termínu alebo opravy), s 3D scénou z Blendera podľa fotiek priestoru.

Živá verzia: https://matuslenicky.github.io/ml-marketing/

## Stav

Pracovná verzia. Stránka má `noindex`, kontakty sú zástupné (`data-contact`) a formulár nič neodosiela na server, len otvorí e-mail návštevníka s vyplnenou správou.

## Ukážky v `ukazky/`

Vymyslené prevádzky, rezervácie sa ukladajú len do `localStorage` prehliadača. Každá ukážka má hore pás, že ide o ukážku, a `noindex`.

Obe ukážky majú len miestnosť, služby a samotnú rezerváciu (bez úvodu, lístka, kontaktov a pätičky).

- `ukazky/restauracia/` – Bistro Kôrka: sála z Blendera, hosť zvolí deň, čas a počet osôb a ťukne na stôl. Kamera sa „presunie“ k stolu a ukáže sálu z miesta hosťa (`assets/pohlad/stol-NN.webp`), vedľa je formulár. Scéna: `blender/scena.py`, spúšťa `blender/render.sh`; polohy stolov v `assets/stoly.json` sú vypočítané v Blenderi. Pohľady hostí: `bash blender/render.sh --view seat --res 1440 --samples 64 --outdir render/pohlady` (kamera sedí na stoličke najďalej od stredu sály a pozerá cez stôl do sály), potom `python tools/prep.py --pohlady blender/render/pohlady`.
- `ukazky/autoservis/` – RAMPA 7: auto na dvojstĺpovom zdviháku, pri skrolovaní vyjde hore (`assets/seq/`). Klik na službu priblíži diel a ukáže detailný záber (`assets/det/det-<služba>.webp`): otvorená kapota s motorom, zložené koleso s kotúčom, regloskop, stanica klimatizácie, diagnostický tablet, výfuk zospodu. V karte služby sa vyberá „S čím máte problém?“ alebo „Neviem príčinu – opíšem“, výber sa prenesie do objednávky aj do `admin.html`. Kapotu `blender/scena.py` vyreže z karosérie modelu `blender/auto.py` (generátor zo susedného projektu `parcela`). Render: `sh blender/blender.sh blender/scena.py --out <dir> --detaily all`, potom `python blender/webp.py <dir>`.

Blender skripty berú zámok `.blender.lock` v koreni repozitára, aby naraz nebežali dva Blendery.

## Ako je to postavené

- `index.html` je celá hlavná stránka, bez buildu. Farby v pomere približne 50 % biela, 40 % kobaltová modrá, 10 % limetkový akcent, len svetlý režim.
- `data-pack` na tlačidlách cenníka sa musí zhodovať s `<option>` vo formulári.
- `assets/fonts`: Wix Madefor Display a Text (SIL OFL), `node tools/fonts.mjs`.
- `assets/img`: zábery prác. `node tools/shots.mjs <dir>` a `node tools/shots-extra.mjs <dir>` (živé weby), `node tools/shots-demos.mjs <dir>` (ukážky v `ukazky/`), prevod na WebP cez `python tools/prep.py`, `prep-extra.py`, `prep-demos.py`.
- `node tools/view.mjs <out.png> <selector> [šírka]` urobí záber časti stránky na kontrolu.
