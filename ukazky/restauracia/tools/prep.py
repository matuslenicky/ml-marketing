# Prevedie rendery z Blenderu (PNG) na WebP pre stránku.
# Spustenie: python tools/prep.py <main.png>
#            python tools/prep.py --pohlady <priečinok so stol-NN.png>   (pohľady hostí od stolov)
#            python tools/prep.py --pano <priečinok so stol-NN-360.png>  (360° panorámy z miesta hosťa)
import sys, os, glob
from PIL import Image

root = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
out = os.path.join(root, 'assets')

def save(img, name, width, quality, **kw):
    if img.width != width:
        img = img.resize((width, round(img.height * width / img.width)), Image.LANCZOS)
    p = os.path.join(out, name)
    img.save(p, 'WEBP', quality=quality, method=6, **kw)
    print(name, img.size, os.path.getsize(p) // 1024, 'kB')

if sys.argv[1] == '--pano':
    os.makedirs(os.path.join(out, 'pohlad'), exist_ok=True)
    for f in sorted(glob.glob(os.path.join(sys.argv[2], 'stol-[0-9][0-9]-360.png'))):
        save(Image.open(f).convert('RGB'), 'pohlad/%s.webp' % os.path.basename(f)[:-4], 2048, 78)
elif sys.argv[1] == '--pohlady':
    os.makedirs(os.path.join(out, 'pohlad'), exist_ok=True)
    for f in sorted(glob.glob(os.path.join(sys.argv[2], 'stol-[0-9][0-9].png'))):
        im = Image.open(f).convert('RGB'); n = os.path.basename(f)[:-4]
        save(im, 'pohlad/%s.webp' % n, 1440, 80)
        save(im, 'pohlad/%s-720.webp' % n, 720, 76)
else:
    main = Image.open(sys.argv[1]).convert('RGBA')
    save(main, 'sala.webp', 1600, 88, alpha_quality=92)
    save(main, 'sala-1000.webp', 1000, 84, alpha_quality=92)
