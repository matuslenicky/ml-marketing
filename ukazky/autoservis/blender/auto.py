# Postaví model auta (bez značky a loga) a uloží ho ako blender/auto.glb.
# Používa generátor karosérií z projektu parcela (car.py + shell.py), ten sa len číta.
#   blender -b --factory-startup -P auto.py -- [priečinok s car.py]
import bpy, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
# Predvolene susedný projekt parcela vedľa ml-marketing (…/parcela/kempy/models).
GEN = argv[0] if argv else os.path.normpath(os.path.join(HERE, '..', '..', '..', '..', 'parcela', 'kempy', 'models'))
sys.path.insert(0, GEN)
import shell
shell.SET['q'] = 1.4                      # jemnejšia sieť, auto je hlavný motív
import car

spec = json.load(open(os.path.join(HERE, 'auto.json'), encoding='utf-8'))
bpy.ops.wm.read_factory_settings(use_empty=True)
root, parts = car.build_car(spec)
bpy.ops.object.select_all(action='DESELECT')
for p in parts: p.select_set(True)
root.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, 'auto.glb'), export_format='GLB', use_selection=True, export_apply=True)
print('DONE auto.glb')
