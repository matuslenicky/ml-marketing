# Prevedie náhľady vlastných ukážok (tools/shots-demos.mjs) na WebP do assets/img a zloží kontrolný hárok.
# Spustenie: python tools/prep-demos.py <priečinok so zábermi>
import sys
from pathlib import Path
from PIL import Image

root = Path(__file__).resolve().parent.parent
shots = Path(sys.argv[1])
out = root / "assets" / "img"
SIZES = {"demo-restauracia": (640, 1120), "demo-autoservis": (640, 1120), "m-restauracia": (390,), "m-autoservis": (390,)}

thumbs = []
for name, widths in SIZES.items():
    im = Image.open(shots / f"{name}.png").convert("RGB")
    for w in widths:
        r = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
        r.save(out / f"{name}-{w}.webp", "WEBP", quality=80, method=6)
    print(name, im.size)
    thumbs.append(im.resize((round(im.width * 420 / im.height), 420), Image.LANCZOS))

sheet = Image.new("RGB", (sum(t.width for t in thumbs) + 10 * (len(thumbs) + 1), 440), "white")
x = 10
for t in thumbs:
    sheet.paste(t, (x, 10))
    x += t.width + 10
sheet.save(shots / "_harok-demos.jpg", quality=82)
