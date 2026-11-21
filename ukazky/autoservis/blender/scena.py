# Dielňa RAMPA 7: auto (auto.glb) v servisnom státí, kamera ide spredu do pohľadu zboku-zhora.
#   blender -b --factory-startup -P scena.py -- --out <priečinok PNG> [--frames all|0,12,23] [--n 24]
#           [--res 1200x900] [--samples 48] [--json body.json] [--still detail] [--blend scena.blend]
# Výstup: <out>/f00.png … a body.json s polohami bodov služieb v koncovom zábere (percentá šírky a výšky).
# Len Cycles na CPU. Materiály vznikajú až po read_factory_settings.
import bpy, bmesh, json, math, os, sys
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def arg(name, default=None):
    return argv[argv.index('--' + name) + 1] if '--' + name in argv else default

OUT = os.path.abspath(arg('out', os.path.join(HERE, 'render')))
N = int(arg('n', '24'))
FRAMES = arg('frames', 'all')
FRAMES = list(range(N)) if FRAMES == 'all' else [int(x) for x in FRAMES.split(',') if x != '']
RX, RY = [int(x) for x in arg('res', '1200x900').split('x')]
SAMPLES = int(arg('samples', '48'))
JSON_OUT = arg('json', os.path.join(OUT, 'body.json'))
STILL = arg('still')
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

# ------------------------------------------------------------------ dvojstĺpový zdvihák v susednom státí
LY = -5.0; LXc = -4.2
for s in (-1, 1):
    y = LY + s * 1.5
    box('zdvihak platna', (LXc, y, .012), (.62, .52, .024), M_steel, .004)
    box('zdvihak stlp', (LXc, y, 1.95), (.3, .34, 3.9), M_lift, .012)
    box('zdvihak vozik', (LXc, y - s * .2, .62), (.36, .1, .62), M_steel, .008)
    box('zdvihak vrch', (LXc, y, 3.86), (.34, .38, .1), M_orange, .008)
    for a in (-1, 1):
        ang = a * .62 * (1 if s < 0 else -1)
        o = box('rameno', (LXc + a * .47, y - s * .52, .43), (1.12, .1, .07), M_steel, .006, rz=ang * s)
        cyl('tanier', (LXc + a * .92, y - s * .93, .49), .075, .04, M_rubber)
box('zdvihak priecnik', (LXc, LY, 3.98), (.22, 3.34, .14), M_lift, .01)
box('zdvihak ovladac', (LXc + .2, LY - 1.5, 1.35), (.12, .22, .3), M_dark, .006)
box('zdvihak tlacidlo', (LXc + .262, LY - 1.5, 1.4), (.01, .06, .06), M_orange)

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
ZC = .1                                             # auto stojí na nájazdovej rampe
WR = .339 + ZC
for o in car_objs:
    if o.parent is None: o.location.z += ZC
# nájazdová rampa (nízky plošinový zdvihák) pod kolesami
for s in (-1, 1):
    box('rampa plosina', (-.05, s * TRK, ZC / 2), (4.9, .64, ZC), M_steel, .008)
    box('rampa hrana', (-.05, s * (TRK + .325), ZC / 2 + .003), (4.9, .03, ZC + .006), M_orange)
    box('rampa nabeh', (2.4 + .345, s * TRK, ZC / 2 - .004), (.71, .64, .014), M_steel, 0, 0, 0, math.atan2(ZC, .69))
    box('rampa doraz', (-2.44, s * TRK, ZC + .04), (.06, .6, .08), M_orange, .006)
box('rampa agregat', (-1.0, 0, .06), (1.6, .5, .1), M_dado, .01)

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

# ------------------------------------------------------------------ body služieb (prázdne objekty na aute)
dg = bpy.context.evaluated_depsgraph_get(); dg.update()
def snap(origin, direction):
    hit, loc, nor, idx, ob, mx = S.ray_cast(dg, Vector(origin), Vector(direction).normalized())
    if not hit: raise RuntimeError('lúč nič netrafil: %r' % (origin,))
    return loc + nor * .01
SPOTS = [
    ('pneumatiky', (XF, -TRK - .14, WR)),
    ('brzdy', (XR, -TRK - .14, WR)),
    ('motor', snap((XF - .02, .02, 3), (0, 0, -1))),
    ('svetla', snap((3.2, -.66, .665 + ZC), (-1, 0, 0))),
    ('klima', snap((.25, -1.4, 1.13 + ZC), (0, 1, 0))),
    ('diagnostika', snap((.42, .3, 3), (0, 0, -1))),
    ('vyfuk', snap((-2.2, -.42, 3), (0, 0, -1))),
]
empties = []
for name, loc in SPOTS:
    e = bpy.data.objects.new('bod ' + name, None); e.empty_display_size = .1; e.location = loc; COL.objects.link(e); empties.append(e)

# ------------------------------------------------------------------ kamera
cd = bpy.data.cameras.new('kamera'); cd.sensor_width = 36; cd.clip_start = .1; cd.clip_end = 80
cam = bpy.data.objects.new('kamera', cd); COL.objects.link(cam); S.camera = cam

def lerp(a, b, t): return a + (b - a) * t
def ease(t): return lerp(t, t * t * (3 - 2 * t), .6)
A = dict(az=0.0, r=6.05, z=.95, tx=.3, ty=0.0, tz=.78, lens=42)
B = dict(az=-49.0, r=7.7, z=4.25, tx=-.05, ty=.1, tz=.42, lens=42)
def pose(t):
    s = ease(t); k = {q: lerp(A[q], B[q], s) for q in A}
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

def spots_json():
    pose(1.0); bpy.context.view_layer.update()
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

if STILL == 'detail':                                # samostatný záber do sekcie o servise: predné koleso a svetlo zblízka
    cam.location = (4.9, -3.2, .68); cd.lens = 52
    cam.rotation_euler = (Vector((1.62, -.5, .6)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    S.render.filepath = os.path.join(OUT, 'detail.png'); bpy.ops.render.render(write_still=True)
else:
    for i in FRAMES:
        pose(i / (N - 1))
        S.render.filepath = os.path.join(OUT, 'f%02d.png' % i)
        bpy.ops.render.render(write_still=True)
        print('ZABER', i)
print('DONE')
