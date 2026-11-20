# Pripraví obrázky ukážok do assets/img (WebP 640 a 1120 px) a kontaktný hárok na kontrolu.
# Spustenie: python tools/prep.py <priečinok so zábermi z tools/shots.mjs>
import sys
from pathlib import Path
from PIL import Image

root = Path(__file__).resolve().parent.parent
shots = Path(sys.argv[1])
out = root / "assets" / "img"
out.mkdir(parents=True, exist_ok=True)

SRC = {p.stem: p for p in shots.glob("*.png")}
# Zdroje zo susedných projektov (priečinky parcela a hlbina vedľa tohto projektu).
SRC["kemp-3d"] = root.parent / "parcela" / "assets" / "kemp-3d.jpg"
SRC["hlbina-detail"] = root.parent / "hlbina" / "assets" / "img" / "detail-1600.webp"
SRC["hlbina-duo"] = root.parent / "hlbina" / "assets" / "img" / "duo-1600.webp"
SRC["hlbina-dusk"] = root.parent / "hlbina" / "assets" / "img" / "dusk-1600.webp"

thumbs = []
for name, path in sorted(SRC.items()):
    im = Image.open(path).convert("RGB")
    for w in (640, 1120):
        if im.width < w:
            continue
        r = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
        r.save(out / f"{name}-{w}.webp", "WEBP", quality=80, method=6)
    print(name, im.size)
    t = im.resize((480, round(im.height * 480 / im.width)), Image.LANCZOS)
    thumbs.append((name, t))

cols = 3
rows = (len(thumbs) + cols - 1) // cols
h = max(t.height for _, t in thumbs)
sheet = Image.new("RGB", (cols * 490 + 10, rows * (h + 10) + 10), "white")
for i, (_, t) in enumerate(thumbs):
    sheet.paste(t, (10 + (i % cols) * 490, 10 + (i // cols) * (h + 10)))
sheet.save(shots / "_harok.jpg", quality=82)
