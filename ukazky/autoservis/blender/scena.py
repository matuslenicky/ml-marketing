# Dielňa RAMPA 7: auto (auto.glb) v servisnom státí, kamera ide spredu do pohľadu zboku-zhora.
#   blender -b --factory-startup -P scena.py -- --out <priečinok PNG> [--frames all|none|0,12,23] [--n 24]
#           [--res 1200x900] [--samples 48] [--json body.json] [--detaily all|motor,brzdy] [--blend scena.blend]
# Auto stojí na dvojstĺpovom zdviháku, pri skrolovaní sa dvíha. --detaily vyrenderuje záber každej služby
# (det-<id>.png): otvorená kapota s motorom, koleso dole s kotúčom, regloskop, stanica klimatizácie, tablet, výfuk zospodu.
# Výstup: <out>/f00.png … a body.json s polohami bodov služieb v koncovom zábere (percentá šírky a výšky).
# Len Cycles na CPU. Materiály vznikajú až po read_factory_settings.
import bpy, bmesh, json, math, os, sys
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view

HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def arg(name, default=None):
    return argv[argv.index('--' + name) + 1] if '--' + name in argv else default

OUT = os.path.abspath(arg('out', os.path.join(HERE, 'render')))
N = int(arg('n', '24'))
FRAMES = arg('frames', 'all')
FRAMES = list(range(N)) if FRAMES == 'all' else [] if FRAMES == 'none' else [int(x) for x in FRAMES.split(',') if x != '']
DETAILY = arg('detaily', '')
RX, RY = [int(x) for x in arg('res', '1200x900').split('x')]
SAMPLES = int(arg('samples', '48'))
JSON_OUT = arg('json', os.path.join(OUT, 'body.json'))
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
S = bpy.context.scene
COL = S.collection

# ------------------------------------------------------------------ farby (zladené so stránkou)
ORANGE = '#ff5a1f'      # signálna oranžová: lak auta, značenie, pás na stene
INK = '#14171b'
GRAPHITE = '#262b32'
STEEL = '#3d444d'

def srgb(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c] + [1.0]

def mat(name, hexc, rough=.5, metal=0.0, coat=0.0, emit=0.0, emit_hex=None):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = srgb(hexc)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if coat:
        b.inputs['Coat Weight'].default_value = coat; b.inputs['Coat Roughness'].default_value = .03
    if emit:
        b.inputs['Emission Color'].default_value = srgb(emit_hex or hexc); b.inputs['Emission Strength'].default_value = emit
    return m

# ------------------------------------------------------------------ pomocné tvary
def finish(o, m, bevel=0.0):
    if m: o.data.materials.append(m)
    if bevel:
        for p in o.data.polygons: p.use_smooth = True
        b = o.modifiers.new('hrana', 'BEVEL'); b.width = bevel; b.segments = 3; b.limit_method = 'ANGLE'
        w = o.modifiers.new('normaly', 'WEIGHTED_NORMAL'); w.keep_sharp = True
    return o

def box(name, c, s, m, bevel=0.0, rz=0.0, rx=0.0, ry=0.0):
    me = bpy.data.meshes.new(name); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1)
    bmesh.ops.scale(bm, vec=Vector(s), verts=bm.verts); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); COL.objects.link(o)
    o.location = c; o.rotation_euler = (rx, ry, rz)
    return finish(o, m, bevel)

def cyl(name, c, r, h, m, axis='z', seg=40, bevel=0.0, r2=None):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r if r2 is None else r2, depth=h)
    bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = len(p.vertices) == 4
    o = bpy.data.objects.new(name, me); COL.objects.link(o); o.location = c
    if axis == 'x': o.rotation_euler = (0, math.pi / 2, 0)
    if axis == 'y': o.rotation_euler = (math.pi / 2, 0, 0)
    if m: me.materials.append(m)
    if bevel:
        b = o.modifiers.new('hrana', 'BEVEL'); b.width = bevel; b.segments = 2; b.limit_method = 'ANGLE'
    return o

def torus(name, c, R, r, m, axis='z', rz=0.0):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    SEG, SEG2 = 40, 14
    rings = []
    for i in range(SEG):
        a = 2 * math.pi * i / SEG; ring = []
        for j in range(SEG2):
            b = 2 * math.pi * j / SEG2
            # sploštený prierez, aby to vyzeralo ako pneumatika a nie ako plávacie koleso
            rr = R + r * max(-.82, min(.82, math.cos(b) * 1.25)); zz = r * 1.15 * math.sin(b)
            ring.append(bm.verts.new((rr * math.cos(a), rr * math.sin(a), zz)))
        rings.append(ring)
    for i in range(SEG):
        A, B = rings[i], rings[(i + 1) % SEG]
        for j in range(SEG2):
            f = bm.faces.new((A[j], B[j], B[(j + 1) % SEG2], A[(j + 1) % SEG2])); f.smooth = True
    bm.normal_update(); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); COL.objects.link(o); o.location = c
    if axis == 'x': o.rotation_euler = (0, math.pi / 2, rz)
    elif axis == 'y': o.rotation_euler = (math.pi / 2, 0, rz)
    me.materials.append(m)
    return o

def text(name, body, loc, rot, size, m, extrude=.004, offset=0.0, align='CENTER'):
    cu = bpy.data.curves.new(name, 'FONT'); cu.body = body; cu.size = size; cu.extrude = extrude; cu.offset = offset
    cu.align_x = align; cu.align_y = 'BOTTOM_BASELINE'
    o = bpy.data.objects.new(name, cu); COL.objects.link(o); o.location = loc; o.rotation_euler = rot
    cu.materials.append(m)
    return o

# ------------------------------------------------------------------ materiály dielne
M_floor = bpy.data.materials.new('podlaha'); M_floor.use_nodes = True
nt = M_floor.node_tree; pb = nt.nodes['Principled BSDF']
tc = nt.nodes.new('ShaderNodeTexCoord')
n1 = nt.nodes.new('ShaderNodeTexNoise'); n1.inputs['Scale'].default_value = .55; n1.inputs['Detail'].default_value = 6
n2 = nt.nodes.new('ShaderNodeTexNoise'); n2.inputs['Scale'].default_value = 9; n2.inputs['Detail'].default_value = 3
cr = nt.nodes.new('ShaderNodeValToRGB')
cr.color_ramp.elements[0].position = .32; cr.color_ramp.elements[0].color = srgb('#4d525a')
cr.color_ramp.elements[1].position = .72; cr.color_ramp.elements[1].color = srgb('#646a73')
mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = .3; mr.inputs['From Max'].default_value = .7
mr.inputs['To Min'].default_value = .16; mr.inputs['To Max'].default_value = .34
nt.links.new(tc.outputs['Object'], n1.inputs['Vector']); nt.links.new(tc.outputs['Object'], n2.inputs['Vector'])
nt.links.new(n1.outputs['Fac'], cr.inputs['Fac']); nt.links.new(cr.outputs['Color'], pb.inputs['Base Color'])
nt.links.new(n2.outputs['Fac'], mr.inputs['Value']); nt.links.new(mr.outputs['Result'], pb.inputs['Roughness'])

M_bay = mat('statie', '#2b3037', .22)
M_line = mat('znacenie', ORANGE, .45)
M_white = mat('znacenie biele', '#e8e6e0', .5)
M_wall = mat('stena', '#4a525d', .8)
M_dado = mat('stena dolu', '#22262c', .6)
M_ceil = mat('strop', '#1a1d21', .9)
M_stripe = mat('pas', ORANGE, .5)
M_steel = mat('ocel', '#31363d', .42, .85)
M_alu = mat('hlinik', '#aeb4ba', .36, .9)
M_gate = mat('brana', '#3a4048', .46, .75)
M_dark = mat('tmavy plast', '#17191c', .55)
M_rubber = mat('guma dielna', '#0f0f10', .82)
M_wood = mat('drevo', '#9a7448', .55)
M_lift = mat('zdvihak', '#d9dbdc', .38, 0, .6)
M_orange = mat('oranzovy lak', ORANGE, .35, 0, .8)
M_peg = mat('tabula', '#c4c7c9', .7)
M_tool = mat('naradie', '#8d949b', .28, 1.0)
M_grip = mat('rukovat', ORANGE, .5)
M_panel = mat('svetelny panel', '#ffffff', .5, emit=9.0, emit_hex='#fff3e2')
M_window = mat('okno brany', '#cfe2f2', .2, emit=2.6, emit_hex='#cfe4ff')
M_screen = mat('obrazovka', '#0b1016', .2, emit=1.4, emit_hex='#ff7a3d')

# ------------------------------------------------------------------ miestnosť
X0, X1, Y0, Y1, HZ = -7.0, 10.0, -8.0, 5.6, 4.8
fl = box('podlaha', ((X0 + X1) / 2, (Y0 + Y1) / 2, -.05), (X1 - X0, Y1 - Y0, .1), M_floor)
box('strop', ((X0 + X1) / 2, (Y0 + Y1) / 2, HZ + .05), (X1 - X0, Y1 - Y0, .1), M_ceil)
DADO = 1.25
for nm, c, s in (('zadna', (X0 - .1, (Y0 + Y1) / 2), (.2, Y1 - Y0)), ('predna', (X1 + .1, (Y0 + Y1) / 2), (.2, Y1 - Y0)),
                 ('prava', ((X0 + X1) / 2, Y1 + .1), (X1 - X0, .2)), ('lava', ((X0 + X1) / 2, Y0 - .1), (X1 - X0, .2))):
    box('stena ' + nm, (c[0], c[1], HZ / 2), (s[0], s[1], HZ), M_wall)
# sokel a oranžový pás na zadnej a pravej stene (tie sú v zábere)
box('sokel zadny', (X0 + .012, (Y0 + Y1) / 2, DADO / 2), (.024, Y1 - Y0, DADO), M_dado)
box('sokel pravy', ((X0 + X1) / 2, Y1 - .012, DADO / 2), (X1 - X0, .024, DADO), M_dado)
box('sokel lavy', ((X0 + X1) / 2, Y0 + .012, DADO / 2), (X1 - X0, .024, DADO), M_dado)
box('pas zadny', (X0 + .016, (Y0 + Y1) / 2, DADO + .06), (.032, Y1 - Y0, .12), M_stripe)
box('pas pravy', ((X0 + X1) / 2, Y1 - .016, DADO + .06), (X1 - X0, .032, .12), M_stripe)
box('pas lavy', ((X0 + X1) / 2, Y0 + .016, DADO + .06), (X1 - X0, .032, .12), M_stripe)

# brána za autom: rám, lamely, pás okien
GW, GH = 4.6, 3.5
box('brana ram L', (X0 + .09, -GW / 2 - .11, GH / 2 + .1), (.18, .22, GH + .2), M_steel, .01)
box('brana ram P', (X0 + .09, GW / 2 + .11, GH / 2 + .1), (.18, .22, GH + .2), M_steel, .01)
box('brana ram H', (X0 + .11, 0, GH + .2), (.22, GW + .44, .4), M_steel, .01)
nsl = 28; sh = GH / nsl
for i in range(nsl):
    z = sh * (i + .5)
    if 17 <= i <= 19: continue
    box('lamela', (X0 + .05, 0, z), (.06, GW, sh - .012), M_gate, .006)
box('okna brany', (X0 + .045, 0, sh * 18.5), (.03, GW, sh * 3 - .012), M_window)
for k in range(1, 6):
    box('priecka okna', (X0 + .06, -GW / 2 + GW * k / 6, sh * 18.5), (.05, .07, sh * 3), M_gate)
# šrafovanie pred bránou
for k in range(16):
    box('srafa', (X0 + .33, -GW / 2 + GW * (k + .5) / 16, .003), (.34, GW / 16 * .55, .006), M_line if k % 2 == 0 else M_bay, rz=.0)

# číslo státia na stene
text('cislo', '7', (X0 + .03, 3.95, 1.72), (math.pi / 2, 0, math.pi / 2), 2.5, M_white, .004, .035)
text('rampa', 'RAMPA', (X0 + .03, 3.95, 3.72), (math.pi / 2, 0, math.pi / 2), .42, M_white, .004, .008)

# ------------------------------------------------------------------ státie pod autom
BX, BY = 3.25, 1.75
box('statie', (0, 0, .0015), (BX * 2, BY * 2, .003), M_bay)
LW = .09
box('ciara 1', (0, -BY, .004), (BX * 2 + LW, LW, .008), M_line)
box('ciara 2', (0, BY, .004), (BX * 2 + LW, LW, .008), M_line)
box('ciara 3', (-BX, 0, .004), (LW, BY * 2, .008), M_line)
for s in (-1, 1):                                   # rohy vpredu, státie je spredu otvorené
    box('roh', (BX, s * (BY - .45), .004), (LW, .9, .008), M_line)
box('stop', (BX + 1.0, 0, .004), (.1, 2.2, .008), M_white)
box('chodnik', (4.9, -4.6, .004), (9.5, .08, .008), M_white)
# susedné státie so zdvihákom

# ------------------------------------------------------------------ pravá stena (y = Y1): pracovný stôl, tabuľa s náradím, skriňa, regál s pneumatikami
WY = Y1 - .42
box('stol doska', (-.4, WY, .93), (3.4, .78, .06), M_wood, .008)
for x in (-1.95, 1.15):
    box('stol noha', (x, WY, .45), (.08, .7, .9), M_steel, .004)
box('stol zasuvky', (.55, WY, .5), (1.05, .7, .8), M_dado, .006)
for k in range(4):
    box('zasuvka', (.55, WY - .355, .2 + k * .19), (.95, .012, .15), M_steel, .004)
    box('zasuvka uchyt', (.55, WY - .372, .245 + k * .19), (.5, .02, .018), M_alu)
box('stol polica', (-1.0, WY, .25), (1.9, .66, .03), M_steel)
box('debna', (-1.35, WY, .38), (.6, .4, .22), M_orange, .01)
box('debna 2', (-.6, WY + .05, .36), (.45, .34, .18), M_dark, .01)
# zverák a veci na stole
box('zverak', (-1.55, WY - .15, 1.03), (.2, .16, .14), M_steel, .01)
box('zverak celust', (-1.55, WY - .28, 1.09), (.16, .05, .1), M_tool, .004)
cyl('zverak vreteno', (-1.55, WY - .36, 1.05), .014, .26, M_tool, 'y')
box('kufrik', (-.5, WY + .05, 1.06), (.52, .3, .2), M_orange, .012)
box('kufrik uchyt', (-.5, WY + .05, 1.175), (.22, .04, .03), M_dark, .004)
for k, (r, h) in enumerate(((.05, .22), (.045, .18), (.055, .26))):
    cyl('sprej', (.25 + k * .15, WY + .15, .96 + h / 2), r, h, (M_dark, M_alu, M_orange)[k])
box('notebook', (1.0, WY - .05, .975), (.36, .26, .02), M_dark, .004)
box('notebook veko', (1.0, WY + .1, 1.09), (.36, .02, .24), M_dark, .004, rx=-.2)
box('notebook obraz', (1.0, WY + .086, 1.09), (.32, .004, .2), M_screen, rx=-.2)
# tabuľa s náradím
PYY = Y1 - .05
box('tabula', (-.4, PYY, 1.95), (3.4, .03, 1.3), M_peg, .004)
for k in range(9):                                  # sada kľúčov podľa veľkosti
    L = .42 - k * .028
    box('kluc', (-1.85 + k * .13, PYY - .03, 2.38 - L / 2), (.034, .012, L), M_tool, .003)
    box('kluc hlava', (-1.85 + k * .13, PYY - .03, 2.38), (.06, .014, .06), M_tool, .003)
for k in range(5):                                  # skrutkovače
    box('skrutkovac', (-.45 + k * .12, PYY - .03, 2.2), (.016, .016, .26), M_tool)
    box('skrutkovac ruk', (-.45 + k * .12, PYY - .03, 2.39), (.04, .04, .13), M_grip, .006)
box('kladivo', (.35, PYY - .03, 2.12), (.03, .025, .44), M_wood)
box('kladivo hlava', (.35, PYY - .03, 2.36), (.17, .05, .06), M_steel, .006)
box('pilka ram', (.85, PYY - .03, 2.3), (.5, .016, .03), M_grip)
box('pilka list', (.85, PYY - .03, 2.16), (.5, .006, .02), M_tool)
for x in (.6, 1.1): box('pilka bok', (x, PYY - .03, 2.23), (.025, .016, .17), M_grip)
for k in range(3):
    cyl('kotuc', (-1.6 + k * .42, PYY - .03, 1.62), .14 - k * .02, .012, M_tool, 'y')
box('uroven', (.55, PYY - .03, 1.55), (1.0, .02, .06), M_orange, .004)
# vysoká skriňa
box('skrina', (2.2, WY + .05, 1.0), (1.0, .6, 2.0), M_dado, .01)
for s in (-1, 1): box('skrina uchyt', (2.2 + s * .06, WY - .262, 1.1), (.02, .02, .3), M_alu)
box('skrina spara', (2.2, WY - .252, 1.0), (.008, .006, 1.9), M_dark)
# regál s pneumatikami
RXc = -4.6
for x in (RXc - 1.25, RXc + 1.25):
    for y in (Y1 - .12, Y1 - .68):
        box('regal stlp', (x, y, 1.45), (.06, .06, 2.9), M_steel)
for z in (.32, 1.25, 2.18):
    for y in (Y1 - .12, Y1 - .68):
        box('regal nosnik', (RXc, y, z), (2.5, .05, .07), M_orange)
    for k in range(8):
        torus('pneu', (RXc - 1.02 + k * .29, Y1 - .4, z + .37), .23, .1, M_rubber, 'x')
# stoh pneumatík a sudy pri zadnej stene vľavo od brány
for k in range(4): torus('pneu stoh', (X0 + .75, -2.95, .11 + k * .225), .23, .1, M_rubber, 'z')
for k in range(3): torus('pneu stoh 2', (-3.3, -3.35, .11 + k * .225), .23, .1, M_rubber, 'z')
for (x, y, m) in ((X0 + .55, -7.2, M_orange), (X0 + .6, -6.45, M_steel), (X0 + 1.25, -7.3, M_dado)):
    cyl('sud', (x, y, .45), .29, .9, m)
    for z in (.3, .6): cyl('sud obruc', (x, y, z), .297, .03, m)
    cyl('sud veko', (x, y, .905), .27, .012, M_steel)
# regál s kanistrami vľavo od brány
# kompresor vpravo od brány
cyl('kompresor', (X0 + .6, 2.95, .55), .26, 1.1, M_orange, 'y')
box('kompresor motor', (X0 + .6, 2.95, .95), (.34, .5, .3), M_dark, .01)
for y in (2.6, 3.3): box('kompresor noha', (X0 + .6, y, .14), (.34, .06, .28), M_steel)

# ------------------------------------------------------------------ dielenský vozík pri aute
def cart(x, y, rz):
    c, s = math.cos(rz), math.sin(rz)
    def P(dx, dy, z): return (x + dx * c - dy * s, y + dx * s + dy * c, z)
    box('vozik telo', P(0, 0, .55), (.78, .46, .8), M_dado, .012, rz)
    box('vozik vrch', P(0, 0, .962), (.82, .5, .03), M_rubber, .006, rz)
    for k in range(5):
        box('vozik zasuvka', P(0, -.232, .22 + k * .15), (.72, .012, .125), M_orange, .004, rz)
        box('vozik uchyt', P(0, -.245, .265 + k * .15), (.6, .016, .016), M_alu, 0, rz)
    box('vozik madlo', P(.44, 0, .86), (.03, .4, .03), M_alu, 0, rz)
    for dx in (-.32, .32):
        for dy in (-.17, .17):
            cyl('vozik koliesko', P(dx, dy, .065), .06, .04, M_rubber, 'y')
    box('vozik miska', P(-.12, .02, .99), (.3, .22, .03), M_alu, .004, rz)
    cyl('vozik racna', P(.2, -.05, .99), .016, .3, M_tool, 'x')
CART = (-2.55, -2.35, .5)
cart(*CART)
# hever pri vozíku
box('hever', (-1.2, -2.75, .09), (.72, .28, .12), M_orange, .02, .2)
cyl('hever tanier', (-.98, -2.7, .17), .06, .04, M_steel)
box('hever rucka', (-1.75, -2.87, .32), (.7, .03, .03), M_steel, 0, .2, 0, -.6)

# ------------------------------------------------------------------ svetlá
def panel(x, y, lx, ly, watts):
    box('panel', (x, y, HZ - .03), (lx + .12, ly + .12, .05), M_steel)
    box('panel svieti', (x, y, HZ - .058), (lx, ly, .006), M_panel)
    ld = bpy.data.lights.new('svetlo', 'AREA'); ld.shape = 'RECTANGLE'; ld.size = lx; ld.size_y = ly; ld.energy = watts
    ld.color = (1.0, .96, .9)
    o = bpy.data.objects.new('svetlo', ld); COL.objects.link(o); o.location = (x, y, HZ - .08)
    try: o.visible_camera = False
    except Exception: pass
for x in (-3.6, 0.0, 3.6):
    panel(x, -1.05, 2.6, .42, 300)                   # dva rady nad autom, pozdĺž karosérie
    panel(x, 1.05, 2.6, .42, 300)
    panel(x, 4.1, 2.6, .42, 300)
    panel(x, -4.4, 2.6, .42, 260)
panel(7.2, 0, .45, 2.2, 220)

W = bpy.data.worlds.new('svet'); S.world = W; W.use_nodes = True
W.node_tree.nodes['Background'].inputs['Color'].default_value = srgb('#39414c')
W.node_tree.nodes['Background'].inputs['Strength'].default_value = .35

# ------------------------------------------------------------------ auto
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'auto.glb'))
car_objs = [o for o in bpy.data.objects if o not in before]
spec = json.load(open(os.path.join(HERE, 'auto.json'), encoding='utf-8'))
CL = spec['L'] / 1000; XF = CL / 2 - spec['fo'] / 1000; XR = XF - spec['wb'] / 1000; TRK = spec['trackF'] / 2000
ZC = 0.0                                            # auto stojí na podlahe medzi stĺpmi zdviháka
WR = .339 + ZC
def tune(name, **kw):
    for m in bpy.data.materials:
        if m.name == name or m.name.startswith(name + '.') or (name.endswith('*') and m.name.startswith(name[:-1])):
            b = m.node_tree.nodes.get('Principled BSDF')
            if not b: continue
            for k, v in kw.items():
                if k == 'color': b.inputs['Base Color'].default_value = srgb(v)
                elif k == 'emit': b.inputs['Emission Strength'].default_value = v
                elif k == 'emit_color': b.inputs['Emission Color'].default_value = srgb(v)
                else:
                    key = {'rough': 'Roughness', 'metal': 'Metallic', 'coat': 'Coat Weight', 'coat_rough': 'Coat Roughness', 'ior': 'IOR'}[k]
                    b.inputs[key].default_value = v
tune('lak *', color='#e63c06', rough=.22, metal=.66, coat=1.0, coat_rough=.02)
tune('sklo', color='#06090c', rough=.015, coat=1.0, coat_rough=.0)
tune('sklo svetle', color='#1c252b', rough=.02, coat=1.0)
tune('lesk cierny', color='#050506', rough=.08, coat=1.0)
tune('guma', color='#0c0c0d', rough=.78)
tune('disk', color='#c4c8cc', rough=.2, metal=1.0)
tune('plast svetly', color='#131517', rough=.6)
tune('disk tmavy', color='#0f1113', rough=.4, metal=.8)
tune('brzda', color='#8c9197', rough=.3, metal=1.0)
tune('led biela', emit=14.0, emit_color='#fff6e8')
tune('led cervena', emit=3.0)
tune('chrom', rough=.06)
tune('svetlo sklo', rough=.02)

# brzdové strmene (oranžové, ladia so značkou servisu)
for X in (XF, XR):
    for s in (-1, 1):
        for k in range(5):
            a = math.radians(180 - 28 + k * 14)
            box('strmen', (X + .17 * math.cos(a), s * (TRK + .03), WR + .17 * math.sin(a)), (.075, .06, .05), M_orange, .006, 0, 0, -a + math.pi / 2)

# ------------------------------------------------------------------ rig auta: všetko, čo sa dvíha so zdvihákom
RIG = bpy.data.objects.new('auto rig', None); COL.objects.link(RIG)
def to_rig(o):
    o.parent = RIG
    return o
for o in car_objs:
    if o.parent is None: to_rig(o)
for o in [o for o in bpy.data.objects if o.name.startswith('strmen')]: to_rig(o)

M_engine = mat('motor blok', '#2b2f35', .45, .7)
M_cover = mat('motor kryt', '#16181b', .35, 0, .3)
M_bayin = mat('motorovy priestor', '#101113', .7)
M_yellow = mat('vicko olej', '#f2c230', .4)
M_blue = mat('vicko ostrekovac', '#2f7bd8', .4)
M_tank = mat('nadrzka', '#e8e4da', .3, 0, 0)
M_pink = mat('chladiaca', '#e8508a', .3)
M_red = mat('plus pol', '#d42a1e', .45)
M_hose = mat('hadica', '#1a1b1d', .6)
M_hblue = mat('hadica modra', '#2563c9', .45)
M_hred = mat('hadica cervena', '#c9302c', .45)
M_pipe = mat('vyfuk', '#6d655d', .5, .8)
M_cat = mat('katalyzator', '#8b8f94', .35, .9)
M_disc = mat('kotuc', '#9aa0a6', .25, 1.0)
M_hub = mat('naboj', '#3b3f45', .45, .8)
M_scrbg = mat('tablet pozadie', '#0d1726', .2, emit=1.2, emit_hex='#13233a')
M_scrok = mat('tablet ok', '#2bd47d', .3, emit=3.0, emit_hex='#2bd47d')
M_scrwarn = mat('tablet chyba', '#ffb020', .3, emit=3.0, emit_hex='#ffb020')
M_scror = mat('tablet listy', ORANGE, .3, emit=2.4, emit_hex=ORANGE)
M_scrtx = mat('tablet text', '#c9d6e6', .3, emit=1.6, emit_hex='#c9d6e6')
M_gauge = mat('manometer', '#f4f4f0', .3)
M_lens = mat('regloskop sosovka', '#cfd8e0', .05, 0, 1.0)

def rig_box(*a, **k): return to_rig(box(*a, **k))
def rig_cyl(*a, **k): return to_rig(cyl(*a, **k))

# ------------------------------------------------------------------ kapota: vyrežeme ju z karosérie, aby sa dala otvoriť
body = max((o for o in car_objs if o.type == 'MESH'), key=lambda o: len(o.data.vertices))
me = body.data; mw = body.matrix_world.copy(); nmat = mw.to_3x3().inverted().transposed()
lak = {i for i, m in enumerate(me.materials) if m and m.name.startswith('lak')}
sklo = {i for i, m in enumerate(me.materials) if m and m.name == 'sklo'}
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
def wc(f): return mw @ f.calc_center_median()
def wn(f): return (nmat @ f.normal).normalized()
ws = [mw @ v.co for f in bm.faces if f.material_index in sklo and wn(f).x > .35 for v in f.verts]
X_COWL = max(p.x for p in ws) + .015
HY, HZ0 = .70, .62                                  # polovičná šírka kapoty, spodná hranica pri nárazníku
# karosériu prerežeme rovnými rovinami, aby mala kapota čisté okraje (nie zuby podľa siete)
mwi = mw.inverted(); m3t = mw.to_3x3().transposed()
for co, no in (((X_COWL, 0, 0), (1, 0, 0)), ((0, HY, 0), (0, 1, 0)), ((0, -HY, 0), (0, 1, 0)), ((0, 0, HZ0), (0, 0, 1))):
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-5,
                           plane_co=mwi @ Vector(co), plane_no=(m3t @ Vector(no)).normalized())
bm.faces.ensure_lookup_table(); bm.edges.ensure_lookup_table(); bm.verts.ensure_lookup_table()
def inside(f):
    c = wc(f)
    return f.material_index in lak and c.x > X_COWL and abs(c.y) < HY and c.z > HZ0
sel = {f.index for f in bm.faces if inside(f)}
hp = [mw @ v.co for i in sel for v in bm.faces[i].verts]
X_HF = max(p.x for p in hp); Z_HLO = min(p.z for p in hp)
Z_HINGE = max(p.z for p in hp if p.x < X_COWL + .08)
print('KAPOTA tvarov %d, pánt x %.3f z %.3f, predok x %.3f, najnižšie z %.3f' % (len(sel), X_COWL, Z_HINGE, X_HF, Z_HLO))
SEAL_EDGES = []                                     # hrany medzi kapotou a zvyškom karosérie: sem príde gumové tesnenie
for e in bm.edges:
    a = sum(1 for f in e.link_faces if f.index in sel)
    if 0 < a < len(e.link_faces):
        SEAL_EDGES.append((mw @ e.verts[0].co, mw @ e.verts[1].co))
hood = body.copy(); hood.data = me.copy(); hood.name = 'kapota'; COL.objects.link(hood)
bm2 = bmesh.new(); bm2.from_mesh(hood.data); bm2.faces.ensure_lookup_table()
bmesh.ops.delete(bm2, geom=[f for f in bm2.faces if f.index not in sel], context='FACES')
bm2.to_mesh(hood.data); bm2.free()
bmesh.ops.delete(bm, geom=[bm.faces[i] for i in sel], context='FACES')
bm.to_mesh(me); bm.free()
sol = hood.modifiers.new('hrubka', 'SOLIDIFY'); sol.thickness = .012; sol.offset = -1
HINGE = bpy.data.objects.new('pant kapoty', None); COL.objects.link(HINGE)
HINGE.location = (X_COWL, 0, Z_HINGE); to_rig(HINGE)
bpy.context.view_layer.update()
hood.parent = HINGE; hood.matrix_parent_inverse = Matrix.Identity(4); hood.matrix_world = mw
def ribbon(name, edges, w, lift):
    verts, faces = [], []
    for p0, q0 in edges:
        d = q0 - p0; d.z = 0
        if d.length < 1e-6: continue
        n = Vector((-d.y, d.x, 0)).normalized() * w; up = Vector((0, 0, lift))
        i = len(verts); verts += [p0 - n + up, p0 + n + up, q0 + n + up, q0 - n + up]; faces.append((i, i + 1, i + 2, i + 3))
    m_ = bpy.data.meshes.new(name); m_.from_pydata(verts, [], faces)
    o = bpy.data.objects.new(name, m_); COL.objects.link(o); m_.materials.append(M_rubber)
    sd = o.modifiers.new('hrubka', 'SOLIDIFY'); sd.thickness = .01; sd.offset = 0
    return o
SEAL_BODY = to_rig(ribbon('skara kapoty', SEAL_EDGES, .006, .001))
SEAL_HOOD = ribbon('tesnenie kapota', SEAL_EDGES, .008, .004)
SEAL_HOOD.parent = HINGE; SEAL_HOOD.matrix_parent_inverse = Matrix.Identity(4); SEAL_HOOD.matrix_world = Matrix.Identity(4)
print('TESNENIE hrán', len(SEAL_EDGES))
# vzpera kapoty
STRUT = cyl('vzpera kapoty', (0, 0, 0), .007, 1.0, M_tool)

# ------------------------------------------------------------------ motorový priestor
ZF = WR - .06                                       # dno priestoru
ZT = Z_HLO - .03                                    # pod najnižším miestom kapoty
XB0, XB1 = X_COWL - .04, X_HF - .16                 # stena za motorom … chladič
BW = HY - .01
rig_box('priestor dno', ((XB0 + XB1) / 2, 0, ZF), (XB1 - XB0, BW * 2, .03), M_bayin)
for s in (-1, 1):
    rig_box('priestor bok', ((XB0 + XB1) / 2, s * BW, (ZF + ZT) / 2), (XB1 - XB0, .03, ZT - ZF), M_bayin)
    rig_box('priestor lem', ((XB0 + XB1) / 2, s * (BW - .02), ZT - .01), (XB1 - XB0 + .02, .07, .02), M_dark)
    rig_box('podbeh', (XF, s * .655, (ZF + .72) / 2), (.86, .21, .72 - ZF), M_bayin, .02)      # zakryje vnútro kolesa
    rig_cyl('tlmic hlava', (XF - .05, s * .64, .735), .07, .03, M_alu, bevel=.006)
rig_box('priestor stena', (XB0, 0, (ZF + Z_HINGE) / 2), (.03, BW * 2, Z_HINGE - ZF), M_bayin)
rig_box('chladic ram', (XB1, 0, (ZF + ZT) / 2), (.05, BW * 2, ZT - ZF), M_dark)
rig_box('chladic', (XB1 - .03, 0, (ZF + ZT) / 2 + .01), (.02, BW * 1.7, (ZT - ZF) * .8), M_steel)
for k in range(9):
    rig_box('chladic rebro', (XB1 - .045, -BW * .8 + k * BW * .2, (ZF + ZT) / 2 + .01), (.01, .012, (ZT - ZF) * .78), M_dark)
HA = ZT - ZF - .04                                  # výška, ktorá je k dispozícii
EX = (XB0 + XB1) / 2 - .02
rig_box('blok motora', (EX, .05, ZF + HA * .32), (.5, .62, HA * .6), M_engine, .02)
rig_box('kryt ventilov', (EX + .01, .05, ZF + HA * .7), (.36, .56, HA * .22), M_cover, .03)
for k in range(5):
    rig_box('rebro krytu', (EX + .01, -.15 + k * .1, ZF + HA * .82), (.3, .02, .012), M_engine, .004)
rig_cyl('vicko oleja', (EX + .12, .26, ZF + HA * .83), .03, .03, M_yellow, bevel=.004)
rig_cyl('sanie', (EX - .2, .05, ZF + HA * .6), .055, .64, M_alu, 'y', bevel=.01)
for k in range(4):
    rig_cyl('sanie rameno', (EX - .12, -.17 + k * .15, ZF + HA * .55), .025, .14, M_alu, 'x')
rig_box('vzduchovy filter', (XB1 - .25, .48, ZF + HA * .62), (.3, .3, HA * .3), M_dark, .025)
rig_cyl('privod vzduchu', (XB1 - .25, .24, ZF + HA * .66), .045, .3, M_hose, 'y')
rig_box('autobateria', (X_COWL + .2, -.5, ZF + HA * .35), (.26, .18, HA * .62), M_dark, .01)
rig_cyl('bateria plus', (X_COWL + .15, -.45, ZF + HA * .68), .018, .03, M_red)
rig_cyl('bateria minus', (X_COWL + .25, -.45, ZF + HA * .68), .018, .03, M_hose)
rig_box('nadrzka chladiva', (X_COWL + .2, .5, ZF + HA * .45), (.16, .2, HA * .5), M_tank, .02)
rig_box('hladina chladiva', (X_COWL + .2, .5, ZF + HA * .38), (.165, .205, HA * .3), M_pink)
rig_cyl('vicko chladiva', (X_COWL + .2, .5, ZF + HA * .72), .035, .03, M_dark)
rig_cyl('vicko ostrekovaca', (XB1 - .12, -.55, ZF + HA * .6), .03, .03, M_blue)
rig_cyl('nadrzka brzd', (X_COWL + .12, -.18, ZF + HA * .6), .04, HA * .25, M_tank)
for (a, b, z) in ((.3, -.3, .5), (-.1, .4, .45)):
    rig_cyl('hadica', (EX + a * .5, b * .6, ZF + HA * z), .02, .4, M_hose, 'x')

# ------------------------------------------------------------------ výfuk pod autom
ZU = .2                                             # pod podlahou karosérie
rig_cyl('vyfuk predny', ((XB0 + XB1) / 2 - .05, .1, ZU + .05), .028, .5, M_pipe, 'x')
rig_cyl('katalyzator', (XB0 - .2, .05, ZU), .065, .45, M_cat, 'x', bevel=.01)
rig_cyl('vyfuk stred', (-.2, -.02, ZU), .028, 2.2, M_pipe, 'x')
rig_cyl('rezonator', (-.3, -.04, ZU - .01), .07, .5, M_cat, 'x', bevel=.01)
rig_box('tlmic zadny', (XR - .55, -.25, ZU + .02), (.6, .38, .17), M_cat, .04)
rig_cyl('vyfuk koncovka', (XR - 1.0, -.42, ZU + .04), .036, .3, M_tool, 'x')
for x in (-.9, .5, XR - .3):
    rig_box('zaves', (x, -.02, ZU + .07), (.03, .05, .08), M_rubber)

# ------------------------------------------------------------------ dvojstĺpový zdvihák v státí
LXc = (XF + XR) / 2 + .05; LYp = 1.48
GC = .14                                            # svetlá výška, sem siahajú tanieriky ramien
LIFT_PARTS = []
for s in (-1, 1):
    y = s * LYp
    box('zdvihak platna', (LXc, y, .012), (.62, .52, .024), M_steel, .004)
    box('zdvihak stlp', (LXc, y, 1.95), (.3, .34, 3.9), M_lift, .012)
    box('zdvihak vrch', (LXc, y, 3.86), (.34, .38, .1), M_orange, .008)
    LIFT_PARTS.append(box('zdvihak vozik', (LXc, y - s * .2, .55), (.36, .1, .62), M_steel, .008))
    for (px, pyy) in ((XF - .5, s * .62), (XR + .42, s * .62)):
        ax, ay = LXc, y - s * .22
        dx, dy = px - ax, pyy - ay; L = math.hypot(dx, dy)
        LIFT_PARTS.append(box('rameno', ((ax + px) / 2, (ay + pyy) / 2, GC - .07), (L, .09, .07), M_steel, .006, math.atan2(dy, dx)))
        LIFT_PARTS.append(cyl('tanier', (px, pyy, GC - .02), .07, .04, M_rubber))
box('zdvihak priecnik', (LXc, 0, 3.98), (.22, LYp * 2 + .34, .14), M_lift, .01)
box('zdvihak ovladac', (LXc + .2, -LYp - .2, 1.35), (.12, .22, .3), M_dark, .006)
box('zdvihak tlacidlo', (LXc + .262, -LYp - .2, 1.4), (.01, .06, .06), M_orange)
LIFT_BASE = [(o, o.location.z) for o in LIFT_PARTS]

# ------------------------------------------------------------------ kolesá: ktoré je ľavé zadné / ľavé predné (strana ku kamere je y < 0)
wheels = [o for o in car_objs if o.name.startswith('koleso')]
def wpos(o):
    bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return sum(bb, Vector()) / 8
W_RL = min(wheels, key=lambda o: wpos(o).x + wpos(o).y)
W_FL = min(wheels, key=lambda o: -wpos(o).x + wpos(o).y)
# kotúč a náboj pod ľavým zadným kolesom (vidno, keď je koleso dole)
BRAKE = [rig_cyl('kotuc', (XR, -TRK + .03, WR), .165, .026, M_disc, 'y', 56),
         rig_cyl('kotuc stred', (XR, -TRK + .02, WR), .085, .05, M_hub, 'y'),
         rig_cyl('naboj', (XR, -TRK - .005, WR), .06, .03, M_tool, 'y')]
for k in range(5):
    a = 2 * math.pi * k / 5
    BRAKE.append(rig_cyl('skrutka', (XR + .05 * math.cos(a), -TRK - .03, WR + .05 * math.sin(a)), .009, .05, M_tool, 'y'))
for o in BRAKE: o.hide_render = True
WHEEL_DOWN = W_RL.copy(); COL.objects.link(WHEEL_DOWN); WHEEL_DOWN.parent = None
WHEEL_DOWN.matrix_world = Matrix.Translation((XR + .15, -TRK - 1.0, .125)) @ Matrix.Rotation(math.pi / 2, 4, 'X') @ Matrix.Translation(-(W_RL.matrix_world.inverted() @ wpos(W_RL)))
WHEEL_DOWN.hide_render = True

# ------------------------------------------------------------------ rekvizity služieb (zobrazujú sa len v detailných záberoch)
PROPS = {k: [] for k in ('pneumatiky', 'svetla', 'klima', 'diagnostika')}
def prop(key, o): PROPS[key].append(o); o.hide_render = True; return o
# nové pneumatiky pri prednom kolese
for k in range(4):
    prop('pneumatiky', torus('nova pneu', (XF - .75, -TRK - 1.25, .11 + k * .225), .23, .1, M_rubber, 'z'))
# regloskop pred ľavým svetlometom
RG = (XF + 1.35, -.62)
prop('svetla', box('regloskop zaklad', (RG[0], RG[1], .06), (.5, .5, .08), M_dark, .01))
prop('svetla', cyl('regloskop stlp', (RG[0] + .12, RG[1], .55), .03, 1.0, M_alu))
prop('svetla', box('regloskop hlava', (RG[0], RG[1], .66), (.42, .36, .3), M_orange, .02))
prop('svetla', cyl('regloskop sosovka', (RG[0] - .215, RG[1], .66), .13, .02, M_lens, 'x'))
prop('svetla', box('regloskop displej', (RG[0] + .05, RG[1], .83), (.2, .22, .03), M_screen))
# servisná stanica klimatizácie pri pravom blatníku
AC = (XF + .1, 1.55)
prop('klima', box('klima stanica', (AC[0], AC[1], .55), (.55, .48, .9), M_orange, .02))
prop('klima', box('klima vrch', (AC[0], AC[1], 1.03), (.57, .5, .06), M_dark, .01))
prop('klima', box('klima displej', (AC[0] - .2, AC[1] - .245, .86), (.004, .22, .14), M_screen, 0, 0, 0, 0))
for k, mm in enumerate((M_hblue, M_hred)):
    prop('klima', cyl('manometer', (AC[0] - .05 + k * .2, AC[1] - .245, .7), .055, .012, M_gauge, 'y'))
    prop('klima', torus('manometer ram', (AC[0] - .05 + k * .2, AC[1] - .25, .7), .058, .008, mm, 'y'))
    for w in (-1, 1):
        prop('klima', cyl('koliesko', (AC[0] + w * .2, AC[1] - .2 + k * .4, .05), .05, .04, M_rubber, 'y'))
def hose(name, pts, m, r=.014):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = r; cu.bevel_resolution = 4
    sp = cu.splines.new('BEZIER'); sp.bezier_points.add(len(pts) - 1)
    for p, c in zip(sp.bezier_points, pts):
        p.co = c; p.handle_left_type = p.handle_right_type = 'AUTO'
    o = bpy.data.objects.new(name, cu); COL.objects.link(o); cu.materials.append(m)
    return o
prop('klima', hose('hadica nizky tlak', [(AC[0] - .05, AC[1] - .2, .98), (AC[0] - .2, AC[1] - .35, 1.25), (X_COWL + .45, .9, ZT + .25), (X_COWL + .32, .45, ZT - .02)], M_hblue))
prop('klima', hose('hadica vysoky tlak', [(AC[0] + .1, AC[1] - .2, .98), (AC[0] + .05, AC[1] - .4, 1.35), (XB1 - .2, .85, ZT + .3), (XB1 - .14, .3, ZT - .02)], M_hred))
# diagnostický tablet na stojane pri dverách vodiča
TB = (1.2, -1.72)
prop('diagnostika', box('stojan zaklad', (TB[0], TB[1], .03), (.42, .42, .04), M_dark, .01))
prop('diagnostika', cyl('stojan tyc', (TB[0], TB[1], .6), .02, 1.15, M_alu))
TAB = prop('diagnostika', box('tablet', (TB[0], TB[1] - .03, 1.2), (.36, .025, .25), M_dark, .01, 0, math.radians(-14), 0))
def scr(x, z, w, h, m):
    o = box('tablet obsah', (0, 0, 0), (w, .002, h), m)
    o.parent = TAB; o.location = (x, -.0135, z); return prop('diagnostika', o)
scr(0, 0, .33, .22, M_scrbg)
scr(0, .095, .33, .03, M_scror)
for k in range(5):
    scr(-.13, .055 - k * .036, .014, .014, M_scrwarn if k == 1 else M_scrok)
    scr(-.06, .055 - k * .036, .1, .007, M_scrtx)
for k, h in enumerate((.05, .08, .065, .11, .09, .12, .07)):
    scr(.035 + k * .02, -.09 + h / 2, .012, h, M_scror if k == 3 else M_scrtx)
prop('diagnostika', hose('kabel obd', [(TB[0] + .1, TB[1] - .02, 1.08), (TB[0] + .05, TB[1] + .1, .7), (.55, -1.0, .45), (.45, -.93, .62)], M_hose, .007))

def worklight(name, loc, watts, size=.25):
    ld = bpy.data.lights.new(name, 'POINT'); ld.energy = watts; ld.shadow_soft_size = size; ld.color = (1.0, .97, .92)
    o = bpy.data.objects.new(name, ld); COL.objects.link(o); o.location = loc
    try: o.visible_camera = False
    except Exception: pass
    o.hide_render = True
    return o
LAMP_BAY = to_rig(worklight('lampa pod kapotou', (EX + .1, -.1, ZT + .45), 40))
LAMP_UNDER = worklight('lampa pod autom', (XR - .3, -.55, 1.0), 90, .4)

# ------------------------------------------------------------------ stav scény: výška zdviháka, kapota, koleso, rekvizity
SHOW = set()
def stav(lift=0.0, kapota=0.0, koleso_dole=False, rekvizity=(), svetla=False, spodok=False):
    RIG.location.z = lift
    for o, z in LIFT_BASE: o.location.z = z + lift
    HINGE.rotation_euler = (0, -math.radians(kapota), 0)
    bpy.context.view_layer.update()
    # vzpera od blatníka k spodku otvorenej kapoty
    if kapota > 1:
        a = Vector((XB1 - .1, -BW + .03, ZT - .02 + lift))
        tip = HINGE.matrix_world @ Vector((X_HF - X_COWL - .25, -BW + .1, -.02))
        d = tip - a
        STRUT.location = (a + tip) / 2; STRUT.scale = (1, 1, d.length)
        STRUT.rotation_euler = d.to_track_quat('Z', 'Y').to_euler(); STRUT.hide_render = False
    else:
        STRUT.hide_render = True
    W_RL.hide_render = koleso_dole; WHEEL_DOWN.hide_render = not koleso_dole
    for o in BRAKE: o.hide_render = not koleso_dole
    for k, objs in PROPS.items():
        for o in objs: o.hide_render = k not in rekvizity
    tune('led biela', emit=60.0 if svetla else 14.0)
    LAMP_BAY.hide_render = kapota < 1
    SEAL_HOOD.hide_render = kapota < 1
    LAMP_UNDER.hide_render = not spodok
    bpy.context.view_layer.update()

# ------------------------------------------------------------------ body služieb (prázdne objekty na aute)
dg = bpy.context.evaluated_depsgraph_get(); dg.update()
def snap(origin, direction):
    hit, loc, nor, idx, ob, mx = S.ray_cast(dg, Vector(origin), Vector(direction).normalized())
    if not hit: raise RuntimeError('lúč nič netrafil: %r' % (origin,))
    return loc + nor * .01
SPOTS = [
    ('pneumatiky', (XF, -TRK - .14, WR)),
    ('brzdy', (XR, -TRK - .14, WR)),
    ('motor', snap((X_HF - .4, .02, 3), (0, 0, -1))),
    ('svetla', snap((3.2, -.66, .665), (-1, 0, 0))),
    ('klima', snap((X_COWL - .1, .45, 3), (0, 0, -1))),
    ('diagnostika', snap((.42, .3, 3), (0, 0, -1))),
    ('vyfuk', snap((-2.2, -.42, 3), (0, 0, -1))),
]
empties = []
for name, loc in SPOTS:
    e = bpy.data.objects.new('bod ' + name, None); e.empty_display_size = .1; e.location = loc; COL.objects.link(e); empties.append(to_rig(e))

# ------------------------------------------------------------------ kamera
cd = bpy.data.cameras.new('kamera'); cd.sensor_width = 36; cd.clip_start = .1; cd.clip_end = 80
cam = bpy.data.objects.new('kamera', cd); COL.objects.link(cam); S.camera = cam

def lerp(a, b, t): return a + (b - a) * t
def ease(t): return lerp(t, t * t * (3 - 2 * t), .6)
A = dict(az=0.0, r=6.05, z=.95, tx=.3, ty=0.0, tz=.78, lens=42)
B = dict(az=-49.0, r=7.7, z=4.25, tx=-.05, ty=.1, tz=.42, lens=42)
LIFT_END = float(arg('lift', '.62'))
def sstep(a, b, x): x = min(1, max(0, (x - a) / (b - a))); return x * x * (3 - 2 * x)
def pose(t):
    zl = LIFT_END * sstep(.12, .9, t)
    stav(lift=zl)
    s = ease(t); k = {q: lerp(A[q], B[q], s) for q in A}
    k['tz'] += zl * .75
    k['z'] = lerp(A['z'], B['z'], s ** 1.35)            # najprv okolo auta, potom hore
    az = math.radians(k['az'])
    tgt = Vector((k['tx'], k['ty'], k['tz']))
    pos = Vector((tgt.x + k['r'] * math.cos(az), tgt.y + k['r'] * math.sin(az), k['z']))
    cam.location = pos; cd.lens = k['lens']
    cam.rotation_euler = (tgt - pos).to_track_quat('-Z', 'Y').to_euler()

# ------------------------------------------------------------------ render
S.render.engine = 'CYCLES'
S.cycles.device = 'CPU'
S.cycles.samples = SAMPLES
S.cycles.use_adaptive_sampling = True; S.cycles.adaptive_threshold = .04
S.cycles.use_denoising = True
try:
    S.cycles.denoiser = 'OPENIMAGEDENOISE'; S.cycles.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
except Exception as e: print('denoiser:', e)
S.cycles.max_bounces = 5; S.cycles.diffuse_bounces = 2; S.cycles.glossy_bounces = 3; S.cycles.transmission_bounces = 2
S.cycles.caustics_reflective = False; S.cycles.caustics_refractive = False
S.cycles.sample_clamp_indirect = 6
S.render.use_persistent_data = True
S.render.resolution_x = RX; S.render.resolution_y = RY; S.render.resolution_percentage = 100
S.render.image_settings.file_format = 'PNG'; S.render.image_settings.color_mode = 'RGB'
for vt in ('Khronos PBR Neutral', 'Standard'):       # farby značky majú vyjsť tak, ako sú na stránke
    try: S.view_settings.view_transform = vt; break
    except Exception: pass
S.view_settings.exposure = float(arg('exposure', '-0.25'))

if arg('blend'):
    pose(1.0); bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(arg('blend')))
cd.dof.aperture_fstop = 2.8

def spots_json():
    pose(1.0); cd.dof.use_dof = False; bpy.context.view_layer.update()
    dg2 = bpy.context.evaluated_depsgraph_get()
    out = []
    for e in empties:
        p = world_to_camera_view(S, cam, e.matrix_world.translation)
        d = (e.matrix_world.translation - cam.matrix_world.translation)
        hit, loc, nor, idx, ob, mx = S.ray_cast(dg2, cam.matrix_world.translation, d.normalized())
        vis = (not hit) or (loc - cam.matrix_world.translation).length > d.length - .06
        out.append({'id': e.name[4:], 'x': round(p.x * 100, 2), 'y': round((1 - p.y) * 100, 2), 'viditelny': bool(vis)})
        print('BOD %-12s x %.1f %%  y %.1f %%  %s' % (e.name[4:], p.x * 100, (1 - p.y) * 100, 'ok' if vis else 'ZAKRYTÝ: ' + (ob.name if ob else '?')))
    json.dump({'zaber': N - 1, 'pomer': [RX, RY], 'body': out}, open(JSON_OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
spots_json()

def look(pos, tgt, lens, dof=None):
    cam.location = pos; cd.lens = lens
    cam.rotation_euler = (Vector(tgt) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
    cd.dof.use_dof = dof is not None
    if dof is not None: cd.dof.focus_distance = (Vector(dof) - Vector(pos)).length
LB = .38; LV = 1.72
DET = {
    'motor':       (dict(kapota=58), ((XF + 1.3, -1.2, 1.78), (EX - .05, .02, ZF + .12), 30, (EX, .05, ZF + HA * .7))),
    'pneumatiky':  (dict(rekvizity=('pneumatiky',)), ((XF + 1.25, -TRK - 1.75, .7), (XF - .1, -TRK - .2, .38), 40, (XF, -TRK - .1, WR))),
    'brzdy':       (dict(lift=LB, koleso_dole=True), ((XR + 1.05, -TRK - 1.55, 1.05), (XR, -TRK - .2, WR + LB - .08), 40, (XR, -TRK, WR + LB))),
    'svetla':      (dict(svetla=True, rekvizity=('svetla',)), ((XF + .75, -2.35, .88), (XF + .8, -.45, .6), 32, (XF + .5, -.62, .66))),
    'klima':       (dict(kapota=58, rekvizity=('klima',)), ((XF + 2.0, 2.7, 1.9), (XF - .3, .35, .72), 30, (XF - .1, .6, ZT))),
    'diagnostika': (dict(rekvizity=('diagnostika',)), ((TB[0] + .3, TB[1] - .85, 1.42), (TB[0] - .12, TB[1] + .45, 1.08), 32, (TB[0], TB[1], 1.2))),
    'vyfuk':       (dict(lift=LV, spodok=True), ((XR - 1.5, -1.95, 1.0), (XR - .2, -.12, LV + .1), 26, (XR - .4, -.3, LV + .2))),
}
for i in FRAMES:
    pose(i / (N - 1))
    S.render.filepath = os.path.join(OUT, 'f%02d.png' % i)
    bpy.ops.render.render(write_still=True)
    print('ZABER', i)
ids = list(DET) if DETAILY == 'all' else [x for x in DETAILY.split(',') if x]
for k in ids:
    st, (pos, tgt, lens, foc) = DET[k]
    stav(**st)
    look(pos, tgt, lens, foc)
    S.render.filepath = os.path.join(OUT, 'det-%s.png' % k)
    bpy.ops.render.render(write_still=True)
    print('DETAIL', k)
print('DONE')
