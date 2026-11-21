# Prevedie rendery z Blenderu (PNG) na WebP pre stránku.
# Spustenie: python tools/prep.py <main.png> [<hero.png>]
import sys, os
from PIL import Image

root = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
out = os.path.join(root, 'assets')

def save(img, name, width, quality, **kw):
    if img.width != width:
        img = img.resize((width, round(img.height * width / img.width)), Image.LANCZOS)
    p = os.path.join(out, name)
    img.save(p, 'WEBP', quality=quality, method=6, **kw)
    print(name, img.size, os.path.getsize(p) // 1024, 'kB')

main = Image.open(sys.argv[1]).convert('RGBA')
save(main, 'sala.webp', 1600, 88, alpha_quality=92)
save(main, 'sala-1000.webp', 1000, 84, alpha_quality=92)
if len(sys.argv) > 2:
    hero = Image.open(sys.argv[2]).convert('RGB')
    save(hero, 'uvod.webp', 1600, 84)
    save(hero, 'uvod-900.webp', 900, 78)
