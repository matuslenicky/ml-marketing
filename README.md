# ML&T Marketing

Firemný web s balíkmi služieb a cenami: rezervácie s mapou pre kempy, weby pre futbalové kluby, weby pre malé firmy a 3D zábery produktov.

Živá verzia: https://matuslenicky.github.io/ml-marketing/

## Stav

Pracovná verzia. Stránka má `noindex`, kontakty v nej sú zástupné (`data-contact`) a formulár nič neodosiela na server, len otvorí e-mail návštevníka s vyplnenou správou.

## Ako je to postavené

- `index.html` je celá stránka, bez buildu. Štýly a skript sú v súbore.
- Farby sú v pomere približne 50 % biela, 40 % kobaltová modrá a 10 % limetkový akcent. Stránka má len svetlý režim.
- Ceny sú na troch miestach, ktoré sa musia zhodovať: pole `AREAS` v skripte (výber balíka v úvode), karty `.pack` v sekciách a `<option>` vo formulári.
- `assets/fonts` obsahuje písma Wix Madefor Display a Wix Madefor Text (licencia SIL OFL), stiahnuté cez `node tools/fonts.mjs`.
- `assets/img` sú zábery vlastných prác: `node tools/shots.mjs <priečinok>` a `node tools/shots-extra.mjs <priečinok>` urobia zábery živých ukážok, `python tools/prep.py <priečinok>` a `python tools/prep-extra.py <priečinok>` ich prevedú na WebP.
- `node tools/view.mjs <out.png> <selector> [šírka]` urobí záber časti stránky na kontrolu.
- `node tools/form-test.mjs <out.png>` vyskúša výber balíka a formulár na mobile.
