# ML&T Marketing

Firemný web: weby pre služby, ktoré žijú z rezervácií a objednávok (výber miesta, termínu alebo opravy), s 3D scénou z Blendera podľa fotiek priestoru.

Živá verzia: https://matuslenicky.github.io/ml-marketing/

## Stav

Pracovná verzia. Stránka má `noindex`, telefón je skutočný, e-mail ešte nie je (po jeho zriadení pridať odkaz s `data-contact="email"` a upraviť text pod formulárom). Formulár nič neodosiela na server: kým e-mail chýba, na mobile otvorí SMS s vyplnenou správou a na počítači ukáže telefón.

## Ukážky v `ukazky/`

Vymyslené prevádzky, rezervácie sa ukladajú len do `localStorage` prehliadača. Každá ukážka má hore pás, že ide o ukážku, a `noindex`.

Obe ukážky majú len miestnosť, služby a samotnú rezerváciu (bez úvodu, lístka, kontaktov a pätičky).

- `ukazky/restauracia/` – Bistro Kôrka: sála z Blendera, hosť zvolí deň, čas a počet osôb a ťukne na stôl. Kamera sa „presunie“ k stolu a ukáže sálu z miesta hosťa (`assets/pohlad/stol-NN.webp`), vedľa je formulár. Scéna: `blender/scena.py`, spúšťa `blender/render.sh`; polohy stolov v `assets/stoly.json` sú vypočítané v Blenderi. Pohľady hostí: `bash blender/render.sh --view seat --res 1440 --samples 64 --outdir render/pohlady` (kamera sedí na stoličke najďalej od stredu sály a pozerá cez stôl do sály), potom `python tools/prep.py --pohlady blender/render/pohlady`. Pohľad od stola je 360° panoráma, ktorou sa otáča ťahaním (WebGL, dobeh po švihnutí; na dotyk len vodorovne): `bash blender/render.sh --view seat --pano --res 2048 --samples 48 --outdir render/pano`, potom `python tools/prep.py --pano blender/render/pano` → `assets/pohlad/stol-NN-360.webp`. Bez WebGL, zo stránky otvorenej z disku (file://) alebo kým panoráma chýba, sa ukáže plochý záber.
- `ukazky/autoservis/` – RAMPA 7: auto na dvojstĺpovom zdviháku, pri skrolovaní vyjde hore (`assets/seq/`). Klik na službu priblíži diel a ukáže detailný záber (`assets/det/det-<služba>.webp`): otvorená kapota s motorom, zložené koleso s kotúčom, regloskop, stanica klimatizácie, diagnostický tablet, výfuk zospodu. V karte služby sa vyberá „S čím máte problém?“ alebo „Neviem príčinu – opíšem“, výber sa prenesie do objednávky aj do `admin.html`. Kapotu `blender/scena.py` vyreže z karosérie modelu `blender/auto.py` (generátor zo susedného projektu `parcela`). Render: `sh blender/blender.sh blender/scena.py --out <dir> --detaily all`, potom `python blender/webp.py <dir>`.

Blender skripty berú zámok `.blender.lock` v koreni repozitára, aby naraz nebežali dva Blendery.

## Ako je to postavené

- `index.html` je celá hlavná stránka, bez buildu. Farby v pomere približne 50 % biela, 40 % kobaltová modrá, 10 % limetkový akcent, len svetlý režim.
- `data-pack` na tlačidlách cenníka sa musí zhodovať s `<option>` vo formulári.
- Písmo hlavnej stránky je systémové (SF Pro na Apple zariadeniach, Segoe UI Variable na Windows 11, Roboto na Androide), vzhľad v duchu Apple: veľké nadpisy s tesným trackingom, mäkké viacvrstvové tiene, zaoblenie 22–36 px. `assets/fonts` (Wix Madefor, SIL OFL, `node tools/fonts.mjs`) hlavná stránka už nenačítava.
- `assets/img`: zábery prác. `node tools/shots.mjs <dir>` a `node tools/shots-extra.mjs <dir>` (živé weby), `node tools/shots-demos.mjs <dir>` (ukážky v `ukazky/`), prevod na WebP cez `python tools/prep.py`, `prep-extra.py`, `prep-demos.py`.
- `node tools/view.mjs <out.png> <selector> [šírka]` urobí záber časti stránky na kontrolu.
