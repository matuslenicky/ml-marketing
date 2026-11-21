# Prevedie vyrenderované PNG na WebP pre stránku a zapíše polohy bodov služieb.
#   python webp.py <priečinok s f00.png … a body.json> [rozpočet sekvencie v kB, predvolene 1750]
# Výstup: ../assets/seq/fNN.webp, ../assets/detail.webp (ak je detail.png), ../assets/body.js a kópia body.json vedľa skriptu.
import glob, io, json, os, shutil, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.abspath(sys.argv[1])
BUDGET = int(sys.argv[2]) * 1024 if len(sys.argv) > 2 else 1750 * 1024
ASSETS = os.path.join(HERE, '..', 'assets')
SEQ = os.path.join(ASSETS, 'seq')
os.makedirs(SEQ, exist_ok=True)

frames = sorted(glob.glob(os.path.join(SRC, 'f[0-9][0-9].png')))
imgs = [Image.open(f).convert('RGB') for f in frames]

def pack(q):
    out = []
    for im in imgs:
        b = io.BytesIO(); im.save(b, 'WEBP', quality=q, method=6); out.append(b.getvalue())
    return out

lo, hi, best = 40, 86, None
while lo <= hi:                                   # najvyššia kvalita, ktorá sa zmestí do rozpočtu
    q = (lo + hi) // 2; data = pack(q); size = sum(len(d) for d in data)
    if size <= BUDGET: best = (q, data); lo = q + 1
    else: hi = q - 1
if best is None: best = (40, pack(40))
q, data = best
for old in glob.glob(os.path.join(SEQ, 'f*.webp')): os.remove(old)
for f, d in zip(frames, data):
    open(os.path.join(SEQ, os.path.basename(f)[:-4] + '.webp'), 'wb').write(d)
print('sekvencia: %d záberov, kvalita %d, spolu %.0f kB' % (len(data), q, sum(len(d) for d in data) / 1024))

det = os.path.join(SRC, 'detail.png')
if os.path.exists(det):
    im = Image.open(det).convert('RGB'); p = os.path.join(ASSETS, 'detail.webp'); im.save(p, 'WEBP', quality=78, method=6)
    print('detail.webp %.0f kB' % (os.path.getsize(p) / 1024))

body = json.load(open(os.path.join(SRC, 'body.json'), encoding='utf-8'))
shutil.copyfile(os.path.join(SRC, 'body.json'), os.path.join(HERE, 'body.json'))
js = {'pocet': len(frames), 'pomer': body['pomer'], 'body': [{'id': b['id'], 'x': b['x'], 'y': b['y']} for b in body['body']]}
open(os.path.join(ASSETS, 'body.js'), 'w', encoding='utf-8', newline='\n').write(
    '/* Polohy bodov služieb v koncovom zábere (percentá šírky a výšky). Vypočítal blender/scena.py cez world_to_camera_view, neupravovať ručne. */\n'
    'window.RAMPA_BODY = ' + json.dumps(js, ensure_ascii=False) + ';\n')
for b in body['body']:
    if not b.get('viditelny', True): print('POZOR: bod %s je v koncovom zábere zakrytý' % b['id'])
print('body.js zapísané')
