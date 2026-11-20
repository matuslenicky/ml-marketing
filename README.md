# ML Marketing

Firemný web s balíkmi služieb a cenami: rezervácie s mapou pre kempy, weby pre futbalové kluby, weby pre malé firmy a 3D zábery produktov.

Živá verzia: https://matuslenicky.github.io/ml-marketing/

## Stav

Pracovná verzia. Stránka má `noindex`, kontakty v nej sú zástupné (`data-contact`) a formulár nič neodosiela na server, len otvorí e-mail návštevníka s vyplnenou správou.

## Ako je to postavené

- `index.html` je celá stránka, bez buildu. Štýly a skript sú v súbore.
- `assets/fonts` obsahuje písma Sora, Funnel Sans a Geist Mono (licencia SIL OFL), stiahnuté cez `node tools/fonts.mjs`.
- `assets/img` sú zábery vlastných prác. Vzniknú cez `node tools/shots.mjs <priečinok>` (zábery živých ukážok) a `python tools/prep.py <priečinok>` (prevod na WebP).
- `node tools/view.mjs <out.png> <selector> [šírka] [dark]` urobí záber časti stránky na kontrolu.

Svetlý a tmavý režim sa riadi nastavením zariadenia, vynútiť sa dá parametrom `?theme=light` alebo `?theme=dark`.
