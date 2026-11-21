# Bistro Kôrka – 3D scéna reštaurácie („domček pre bábiky“) pre ukážku rezervácie stolov.
#
# Spustenie (Blender 5.2, len Cycles na CPU):
#   blender -b --factory-startup -P scena.py -- --view main --res 1600 --samples 160 \
#       --out render/main.png --json ../assets/stoly.json
#   blender -b --factory-startup -P scena.py -- --view hero --res 1600 --samples 160 --out render/hero.png
#
# --view main  pohľad zhora zošikma na celú sálu (priehľadné pozadie) + JSON s polohami stolov
# --view hero  záber z výšky očí pri stole (so stropom)
# Polohy stolov v JSON sú v percentách obrázka (world_to_camera_view), nič sa neodhaduje ručne.

import bpy, bmesh, sys, json, math, os, random
from math import radians, sin, cos, pi, atan2
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def arg(name, default):
    return argv[argv.index(name) + 1] if name in argv else default

VIEW = arg('--view', 'main')
RES = int(arg('--res', '480'))
SAMPLES = int(arg('--samples', '24'))
OUT = os.path.abspath(arg('--out', 'test.png'))
JSON_OUT = arg('--json', '')
ASPECT = 1100 / 1600 if VIEW == 'main' else 1000 / 1600

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
COL = scene.collection
random.seed(11)

# ---------------------------------------------------------------- materiály
def lin(h):
    h = h.lstrip('#')
    def f(c):
        c = int(c, 16) / 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return (f(h[0:2]), f(h[2:4]), f(h[4:6]), 1.0)

def base_mat(name):
    m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:
        pass
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    return m, nt, out

def set_in(node, name, value):
    if name in node.inputs:
        node.inputs[name].default_value = value

def pbr(name, color, rough=0.5, metal=0.0, sheen=0.0, coat=0.0, transmission=0.0, alpha=1.0, emit=None, emit_s=0.0):
    m, nt, out = base_mat(name)
    b = nt.nodes.new('ShaderNodeBsdfPrincipled')
    set_in(b, 'Base Color', lin(color))
    set_in(b, 'Roughness', rough)
    set_in(b, 'Metallic', metal)
    set_in(b, 'Sheen Weight', sheen)
    set_in(b, 'Coat Weight', coat)
    set_in(b, 'Transmission Weight', transmission)
    set_in(b, 'Alpha', alpha)
    if emit:
        set_in(b, 'Emission Color', lin(emit))
        set_in(b, 'Emission Strength', emit_s)
    nt.links.new(b.outputs[0], out.inputs[0])
    return m

def emission(name, color, strength):
    m, nt, out = base_mat(name)
    e = nt.nodes.new('ShaderNodeEmission')
    e.inputs[0].default_value = lin(color)
    e.inputs[1].default_value = strength
    nt.links.new(e.outputs[0], out.inputs[0])
    return m

def wood(name, c1, c2, rough=0.42, grain=(1.2, 16.0, 1.2), nscale=2.5, coat=0.0):
    m, nt, out = base_mat(name)
    b = nt.nodes.new('ShaderNodeBsdfPrincipled')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = grain
    nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = nscale
    nz.inputs['Detail'].default_value = 5.0
    cr = nt.nodes.new('ShaderNodeValToRGB')
    cr.color_ramp.elements[0].position = 0.32
    cr.color_ramp.elements[0].color = lin(c1)
    cr.color_ramp.elements[1].position = 0.68
    cr.color_ramp.elements[1].color = lin(c2)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    nt.links.new(mp.outputs[0], nz.inputs['Vector'])
    nt.links.new(nz.outputs[0], cr.inputs[0])
    nt.links.new(cr.outputs[0], b.inputs['Base Color'])
    set_in(b, 'Roughness', rough)
    set_in(b, 'Coat Weight', coat)
    nt.links.new(b.outputs[0], out.inputs[0])
    return m

def planks(name, c1, c2, mortar, width=1.3, row=0.15, rough=0.45, rot=0.0):
    m, nt, out = base_mat(name)
    b = nt.nodes.new('ShaderNodeBsdfPrincipled')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Rotation'].default_value = (0, 0, rot)
    br = nt.nodes.new('ShaderNodeTexBrick')
    br.offset = 0.37
    br.inputs['Scale'].default_value = 1.0
    br.inputs['Mortar Size'].default_value = 0.004
    br.inputs['Brick Width'].default_value = width
    br.inputs['Row Height'].default_value = row
    br.inputs['Mortar'].default_value = lin(mortar)
    br.inputs['Bias'].default_value = 0.0
    mp2 = nt.nodes.new('ShaderNodeMapping')
    mp2.inputs['Rotation'].default_value = (0, 0, rot)
    mp2.inputs['Scale'].default_value = (1.0, 14.0, 1.0)
    nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 1.6
    nz.inputs['Detail'].default_value = 4.0
    ra = nt.nodes.new('ShaderNodeValToRGB')
    ra.color_ramp.elements[0].position = 0.3
    ra.color_ramp.elements[0].color = lin(c1)
    ra.color_ramp.elements[1].position = 0.7
    ra.color_ramp.elements[1].color = lin(c2)
    rb = nt.nodes.new('ShaderNodeValToRGB')
    rb.color_ramp.elements[0].position = 0.3
    rb.color_ramp.elements[0].color = lin(c2)
    rb.color_ramp.elements[1].position = 0.7
    rb.color_ramp.elements[1].color = lin(c1)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    nt.links.new(tc.outputs['Object'], mp2.inputs['Vector'])
    nt.links.new(mp.outputs[0], br.inputs['Vector'])
    nt.links.new(mp2.outputs[0], nz.inputs['Vector'])
    nt.links.new(nz.outputs[0], ra.inputs[0])
    nt.links.new(nz.outputs[0], rb.inputs[0])
    nt.links.new(ra.outputs[0], br.inputs['Color1'])
    nt.links.new(rb.outputs[0], br.inputs['Color2'])
    nt.links.new(br.outputs[0], b.inputs['Base Color'])
    set_in(b, 'Roughness', rough)
    nt.links.new(b.outputs[0], out.inputs[0])
    return m

def dusk(name, strength):
    m, nt, out = base_mat(name)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sp = nt.nodes.new('ShaderNodeSeparateXYZ')
    mr = nt.nodes.new('ShaderNodeMapRange')
    mr.inputs['From Min'].default_value = 0.3
    mr.inputs['From Max'].default_value = 2.4
    cr = nt.nodes.new('ShaderNodeValToRGB')
    els = cr.color_ramp.elements
    els[0].position = 0.0
    els[0].color = lin('#F0A35E')
    els[1].position = 1.0
    els[1].color = lin('#22386B')
    e = els.new(0.42)
    e.color = lin('#C98F8A')
    e = els.new(0.7)
    e.color = lin('#4F6CA6')
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs[1].default_value = strength
    nt.links.new(tc.outputs['Object'], sp.inputs[0])
    nt.links.new(sp.outputs[2], mr.inputs['Value'])
    nt.links.new(mr.outputs[0], cr.inputs[0])
    nt.links.new(cr.outputs[0], em.inputs[0])
    nt.links.new(em.outputs[0], out.inputs[0])
    return m

M = {}
def mk():
    M['base'] = pbr('zaklad', '#2A211B', 0.8)
    M['floor'] = planks('podlaha', '#B4855A', '#9C6F47', '#4A3222', 1.25, 0.14, 0.42)
    M['deck'] = planks('terasa', '#8E7257', '#7B6049', '#3A2B20', 2.4, 0.12, 0.6, rot=pi / 2)
    M['wall'] = pbr('stena', '#E9DDC6', 0.9)
    M['wains'] = pbr('oblozenie', '#2D4A3D', 0.55)
    M['walnut'] = wood('orech', '#5A3923', '#75492C', 0.4)
    M['oak'] = wood('dub', '#C39A6C', '#AE8457', 0.38, coat=0.2)
    M['oakdark'] = wood('dub_tmavy', '#8A6140', '#9E7149', 0.4, coat=0.2)
    M['velvet'] = pbr('zamat', '#2B5646', 0.85, sheen=0.6)
    M['ochre'] = pbr('okrova', '#C8902E', 0.85, sheen=0.4)
    M['terra'] = pbr('tehlova', '#B25838', 0.85, sheen=0.3)
    M['linen'] = pbr('lan', '#E7DCC6', 0.9, sheen=0.3)
    M['cognac'] = pbr('koza', '#9A5A2E', 0.55)
    M['brass'] = pbr('mosadz', '#C9A04A', 0.28, metal=1.0)
    M['black'] = pbr('kov', '#201D1B', 0.45, metal=0.6)
    M['plate'] = pbr('tanier', '#F4EFE5', 0.25)
    M['glass'] = pbr('sklo', '#EAF2F0', 0.03, transmission=1.0)
    M['pane'] = pbr('okno', '#CFE0E6', 0.02, transmission=1.0)
    M['tealight'] = pbr('kahanec', '#F2B45A', 0.3, emit='#FFB14A', emit_s=5.0)
    M['bulb'] = emission('ziarovka', '#FFC98A', 14.0)
    M['globe'] = emission('gula', '#FFD9A8', 6.0)
    M['neon'] = emission('napis', '#FFD08A', 7.0)
    M['led'] = emission('led', '#FFC27A', 4.0)
    M['dusk'] = dusk('sumrak', 1.3 if VIEW == 'main' else 2.2)
    M['leaf1'] = pbr('list1', '#3E6B3A', 0.55)
    M['leaf2'] = pbr('list2', '#2D5732', 0.55)
    M['leaf3'] = pbr('list3', '#5B8443', 0.55)
    M['pot'] = pbr('kvetinac', '#A9603F', 0.8)
    M['potdark'] = pbr('kvetinac_tmavy', '#34312D', 0.7)
    M['soil'] = pbr('hlina', '#2A1F18', 1.0)
    M['tile'] = pbr('obklad', '#1F4B43', 0.18, coat=0.5)
    M['rug1'] = pbr('koberec1', '#A9553A', 0.95, sheen=0.5)
    M['rug2'] = pbr('koberec2', '#D9C29A', 0.95, sheen=0.5)
    M['rug3'] = pbr('koberec3', '#35584B', 0.95, sheen=0.5)
    M['chrome'] = pbr('chrom', '#C9CCD0', 0.2, metal=1.0)
    M['art1'] = pbr('obraz1', '#D7A441', 0.8)
    M['art2'] = pbr('obraz2', '#B5553A', 0.8)
    M['art3'] = pbr('obraz3', '#EDE3CF', 0.8)
    M['art4'] = pbr('obraz4', '#2F5B4C', 0.8)
    M['chalk'] = pbr('tabula', '#26302C', 0.9)
    for i, c in enumerate(['#6B3A16', '#1E4A2C', '#C9D8D2', '#3A1A12', '#A8742A', '#7A2A22']):
        M['btl%d' % i] = pbr('flasa%d' % i, c, 0.08, transmission=0.6)
    M['ceiling'] = pbr('strop', '#33473D', 0.9)
mk()

# ---------------------------------------------------------------- stavebnica sietí
I4 = Matrix.Identity(4)

class MB:
    def __init__(self, name):
        self.name = name
        self.bm = bmesh.new()
        self.mats = []

    def _tag(self, verts, mat, smooth=False):
        if mat not in self.mats:
            self.mats.append(mat)
        mi = self.mats.index(mat)
        faces = set()
        for v in verts:
            for f in v.link_faces:
                faces.add(f)
        for f in faces:
            f.material_index = mi
            f.smooth = smooth
        return faces

    def box(self, size, loc, mat, rz=0.0, rx=0.0, ry=0.0):
        m = (Matrix.Translation(loc) @ Matrix.Rotation(rz, 4, 'Z') @ Matrix.Rotation(ry, 4, 'Y')
             @ Matrix.Rotation(rx, 4, 'X') @ Matrix.Diagonal((size[0], size[1], size[2], 1.0)))
        r = bmesh.ops.create_cube(self.bm, size=1.0, matrix=m)
        self._tag(r['verts'], mat)

    def cyl(self, r, h, loc, mat, r2=None, segs=20, caps=True, rot=None, smooth=True):
        m = Matrix.Translation(loc) @ (rot or I4)
        res = bmesh.ops.create_cone(self.bm, cap_ends=caps, cap_tris=False, segments=segs,
                                    radius1=r, radius2=(r if r2 is None else r2), depth=h, matrix=m)
        faces = self._tag(res['verts'], mat, smooth)
        if smooth:
            for f in faces:
                if len(f.verts) > 4:
                    f.smooth = False
                    for e in f.edges:
                        e.smooth = False

    def sphere(self, r, loc, mat, scale=(1, 1, 1), sub=2):
        m = Matrix.Translation(loc) @ Matrix.Diagonal((scale[0], scale[1], scale[2], 1.0))
        res = bmesh.ops.create_icosphere(self.bm, subdivisions=sub, radius=r, matrix=m)
        self._tag(res['verts'], mat, True)

    def poly(self, pts, mat, smooth=False):
        vs = [self.bm.verts.new(p) for p in pts]
        f = self.bm.faces.new(vs)
        if mat not in self.mats:
            self.mats.append(mat)
        f.material_index = self.mats.index(mat)
        f.smooth = smooth
        return vs

    def leaf(self, base, az, el, L, W, mat, droop=0.0):
        d = Vector((cos(az) * cos(el), sin(az) * cos(el), sin(el)))
        side = Vector((-sin(az), cos(az), 0.0))
        up = side.cross(d)
        base = Vector(base)
        tip = base + d * L + Vector((0, 0, -droop * L))
        mid = base + d * L * 0.45 + Vector((0, 0, -droop * L * 0.25))
        l = mid + side * W / 2 + up * W * 0.14
        r = mid - side * W / 2 + up * W * 0.14
        if mat not in self.mats:
            self.mats.append(mat)
        mi = self.mats.index(mat)
        vb, vl, vt, vr = [self.bm.verts.new(p) for p in (base, l, tip, r)]
        for f in (self.bm.faces.new((vb, vl, vt)), self.bm.faces.new((vb, vt, vr))):
            f.material_index = mi

    def mesh(self):
        me = bpy.data.meshes.new(self.name)
        self.bm.normal_update()
        self.bm.to_mesh(me)
        self.bm.free()
        for m in self.mats:
            me.materials.append(m)
        return me

    def obj(self, loc=(0, 0, 0), rz=0.0, bevel=0.0):
        return inst(self.mesh(), self.name, loc, rz, bevel)

def inst(me, name, loc=(0, 0, 0), rz=0.0, bevel=0.0):
    o = bpy.data.objects.new(name, me)
    COL.objects.link(o)
    o.location = loc
    o.rotation_euler = (0, 0, rz)
    if bevel:
        mod = o.modifiers.new('hrany', 'BEVEL')
        mod.width = bevel
        mod.segments = 2
        mod.limit_method = 'ANGLE'
        mod.angle_limit = radians(50)
    return o

RX, RY, WH, WT = 10.8, 7.5, 2.6, 0.22
TABLES = []
LIGHTS = []
PEND = float(arg('--pend', '1.6'))

def point(loc, power, color=(1.0, 0.72, 0.42), size=0.06):
    l = bpy.data.lights.new('svetlo', 'POINT')
    l.energy = power
    l.color = color
    l.shadow_soft_size = size
    o = bpy.data.objects.new('svetlo', l)
    o.location = loc
    COL.objects.link(o)
    LIGHTS.append(o)
    return o

# ---------------------------------------------------------------- nábytok
def chair_mesh(name, frame, fabric):
    mb = MB(name)
    for sx in (-1, 1):
        mb.box((0.036, 0.036, 0.44), (sx * 0.19, 0.17, 0.22), frame)
        mb.box((0.036, 0.036, 0.88), (sx * 0.19, -0.2, 0.44), frame)
    mb.box((0.44, 0.43, 0.035), (0, -0.005, 0.445), frame)
    mb.box((0.42, 0.41, 0.045), (0, 0.0, 0.485), fabric)
    mb.box((0.40, 0.032, 0.21), (0, -0.203, 0.76), fabric)
    return mb.mesh()

def stool_mesh(name, frame, fabric):
    mb = MB(name)
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.box((0.03, 0.03, 0.74), (sx * 0.13, sy * 0.13, 0.37), frame)
    mb.box((0.29, 0.03, 0.025), (0, 0.13, 0.27), frame)
    mb.box((0.29, 0.03, 0.025), (0, -0.13, 0.27), frame)
    mb.box((0.03, 0.29, 0.025), (0.13, 0, 0.27), frame)
    mb.box((0.03, 0.29, 0.025), (-0.13, 0, 0.27), frame)
    mb.cyl(0.175, 0.06, (0, 0, 0.77), fabric, segs=24)
    return mb.mesh()

CH = {}
def chairs_init():
    CH['a'] = chair_mesh('stolicka_zelena', M['walnut'], M['velvet'])
    CH['b'] = chair_mesh('stolicka_okrova', M['walnut'], M['ochre'])
    CH['c'] = chair_mesh('stolicka_lan', M['oakdark'], M['linen'])
    CH['t'] = chair_mesh('stolicka_terasa', M['black'], M['terra'])
    CH['s'] = stool_mesh('barova', M['black'], M['cognac'])
    CH['s2'] = stool_mesh('barova2', M['walnut'], M['velvet'])

def seat(kind, x, y, tx, ty, z=0.0):
    rz = atan2(ty - y, tx - x) - pi / 2
    o = inst(CH[kind], 'sedenie', (x, y, z), rz, 0.006)
    return o

def setting(mb, px, py, dx, dy, h, napkin):
    # tanier, pohár a obrúsok pred jedným hosťom; (dx, dy) je smer od hosťa k stredu stola
    mb.cyl(0.115, 0.012, (px, py, h + 0.006), M['plate'], segs=20)
    mb.cyl(0.075, 0.006, (px, py, h + 0.0145), M['plate'], segs=16)
    rx_, ry_ = dy, -dx
    mb.cyl(0.03, 0.09, (px + rx_ * 0.15 + dx * 0.09, py + ry_ * 0.15 + dy * 0.09, h + 0.045), M['glass'], segs=10)
    mb.box((0.055, 0.15, 0.008), (px - rx_ * 0.165, py - ry_ * 0.165, h + 0.004), napkin, rz=atan2(dy, dx) + pi / 2)

def centerpiece(mb, x, y, h, vase=True):
    mb.cyl(0.035, 0.06, (x, y, h + 0.03), M['tealight'], segs=12)
    if vase:
        mb.cyl(0.028, 0.11, (x + 0.11, y + 0.04, h + 0.055), M['plate'], r2=0.018, segs=10)
        for i in range(5):
            mb.leaf((x + 0.11, y + 0.04, h + 0.1), random.uniform(0, 2 * pi), radians(random.uniform(50, 80)),
                    random.uniform(0.1, 0.17), 0.045, M[random.choice(['leaf1', 'leaf3'])])

def register(tid, seats, zone, kde, tvar, pts, cx, cy, z):
    TABLES.append(dict(id=tid, seats=seats, zone=zone, kde=kde, tvar=tvar,
                       pts=[Vector((x, y, z)) for x, y in pts], c=Vector((cx, cy, z))))

def table_rect(tid, seats, zone, kde, cx, cy, w, d, sides, h=0.75, top='oak', legs='legs', chair='a',
               napkin='ochre', plates=None, runner=False, tvar='obdĺžnikový', deco=True, z0=0.0):
    mb = MB('stol%d' % tid)
    mb.box((w, d, 0.045), (cx, cy, z0 + h - 0.0225), M[top])
    if legs == 'legs':
        for sx in (-1, 1):
            for sy in (-1, 1):
                mb.box((0.06, 0.06, h - 0.045), (cx + sx * (w / 2 - 0.09), cy + sy * (d / 2 - 0.09), z0 + (h - 0.045) / 2), M[top])
    else:
        mb.cyl(0.045, h - 0.07, (cx, cy, z0 + 0.025 + (h - 0.07) / 2), M['black'], segs=14)
        mb.cyl(0.24, 0.025, (cx, cy, z0 + 0.0125), M['black'], segs=24)
    hz = z0 + h
    if runner:
        mb.box((w - 0.25, 0.3, 0.006), (cx, cy, hz + 0.003), M['linen'])
        hz2 = hz + 0.006
    else:
        hz2 = hz
    for side, n in sides.items():
        for i in range(n):
            t = (i + 0.5) / n
            if side in 'NS':
                s = 1 if side == 'N' else -1
                x = cx - w / 2 + t * w
                y = cy + s * (d / 2 + 0.27)
                dx, dy = 0.0, -s
            else:
                s = 1 if side == 'E' else -1
                x = cx + s * (w / 2 + 0.27)
                y = cy - d / 2 + t * d
                dx, dy = -s, 0.0
            seat(chair, x, y, x + dx, y + dy, z0)
            setting(mb, x + dx * 0.47, y + dy * 0.47, dx, dy, hz, M[napkin])
    for (px, py, dx, dy) in (plates or []):
        setting(mb, px, py, dx, dy, hz, M[napkin])
    if deco:
        if w > 2.0:
            for ox in (-0.75, 0.0, 0.75):
                centerpiece(mb, cx + ox, cy, hz2, vase=(ox != 0.0))
        else:
            centerpiece(mb, cx - 0.04, cy, hz2, vase=(w >= 1.0 or d >= 1.0))
    mb.obj(bevel=0.008)
    pts = [(cx - w / 2, cy - d / 2), (cx + w / 2, cy - d / 2), (cx + w / 2, cy + d / 2), (cx - w / 2, cy + d / 2)]
    register(tid, seats, zone, kde, tvar, pts, cx, cy, hz)

def table_round(tid, seats, zone, kde, cx, cy, r, n, h=0.75, top='oak', chair='a', napkin='ochre',
                kind='chair', a0=0.0, tvar='okrúhly', z0=0.0):
    mb = MB('stol%d' % tid)
    mb.cyl(r, 0.045, (cx, cy, z0 + h - 0.0225), M[top], segs=40)
    mb.cyl(0.05, h - 0.07, (cx, cy, z0 + 0.025 + (h - 0.07) / 2), M['black'], segs=14)
    mb.cyl(min(0.34, r * 0.62), 0.025, (cx, cy, z0 + 0.0125), M['black'], segs=24)
    hz = z0 + h
    for i in range(n):
        a = a0 + i * 2 * pi / n
        dist = r + (0.27 if kind == 'chair' else 0.2)
        x, y = cx + cos(a) * dist, cy + sin(a) * dist
        seat(chair, x, y, cx, cy, z0)
        if r >= 0.45:
            setting(mb, cx + cos(a) * (r - 0.2), cy + sin(a) * (r - 0.2), -cos(a), -sin(a), hz, M[napkin])
        else:
            mb.cyl(0.03, 0.09, (cx + cos(a) * (r - 0.14), cy + sin(a) * (r - 0.14), hz + 0.045), M['glass'], segs=10)
    centerpiece(mb, cx, cy, hz, vase=(r >= 0.45))
    mb.obj(bevel=0.008)
    pts = [(cx + cos(i * 2 * pi / 28) * r, cy + sin(i * 2 * pi / 28) * r) for i in range(28)]
    register(tid, seats, zone, kde, tvar, pts, cx, cy, hz)

def pendant(x, y, zb=1.72, style=0, power=55.0, r=0.2, ztop=None):
    power *= PEND
    ztop = WH if ztop is None else ztop
    mat = [M['brass'], M['black'], M['ochre'], M['wains']][style % 4]
    mb = MB('lampa')
    mb.cyl(0.006, ztop - (zb + 0.2), (x, y, (ztop + zb + 0.2) / 2), M['black'], segs=6)
    mb.cyl(r, 0.2, (x, y, zb + 0.1), mat, r2=0.05, segs=28, caps=False)
    mb.cyl(0.05, 0.035, (x, y, zb + 0.215), mat, segs=16)
    mb.sphere(0.04, (x, y, zb + 0.11), M['bulb'], sub=1)
    mb.obj()
    point((x, y, zb + 0.03), power)

def plant(x, y, kind='fig', z=0.0, pot_r=0.19, pot_h=0.38, pot='pot', height=1.5, n=26, seed=1):
    rnd = random.Random(seed * 97 + int(x * 10) + int(y * 100))
    greens = [M['leaf1'], M['leaf2'], M['leaf3']]
    mb = MB('rastlina')
    mb.cyl(pot_r * 0.72, pot_h, (x, y, z + pot_h / 2), M[pot], r2=pot_r, segs=18)
    mb.cyl(pot_r * 0.9, 0.01, (x, y, z + pot_h - 0.015), M['soil'], segs=18)
    top = z + pot_h
    if kind == 'fig':
        mb.cyl(0.018, height - pot_h, (x, y, top + (height - pot_h) / 2 - 0.05), M['walnut'], segs=6)
        for i in range(n):
            hz = top + 0.25 + (height - pot_h - 0.2) * (i / n) ** 0.8
            az = i * 2.4 + rnd.uniform(-0.3, 0.3)
            mb.leaf((x, y, hz), az, radians(rnd.uniform(5, 45)), rnd.uniform(0.3, 0.42), rnd.uniform(0.17, 0.24),
                    rnd.choice(greens), droop=rnd.uniform(0.05, 0.3))
    elif kind == 'palm':
        for i in range(n):
            az = i * 2.4 + rnd.uniform(-0.3, 0.3)
            el = radians(rnd.uniform(35, 80))
            mb.leaf((x + cos(az) * 0.04, y + sin(az) * 0.04, top - 0.02), az, el, rnd.uniform(0.5, 1.0) * (height - pot_h),
                    rnd.uniform(0.1, 0.16), rnd.choice(greens), droop=rnd.uniform(0.1, 0.4))
    elif kind == 'trail':
        for i in range(n):
            az = rnd.uniform(0, 2 * pi)
            el = radians(rnd.uniform(-70, 40))
            mb.leaf((x + cos(az) * pot_r * 0.6, y + sin(az) * pot_r * 0.6, top), az, el, rnd.uniform(0.15, 0.45),
                    rnd.uniform(0.07, 0.11), rnd.choice(greens), droop=rnd.uniform(0.2, 0.6))
    mb.obj()

def planter(x0, y0, x1, y1, h=0.42, z=0.0, seed=3, tall=0.45):
    rnd = random.Random(seed)
    greens = [M['leaf1'], M['leaf2'], M['leaf3']]
    mb = MB('truhlik')
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    mb.box((x1 - x0, y1 - y0, h), (cx, cy, z + h / 2), M['walnut'])
    mb.box((x1 - x0 - 0.05, y1 - y0 - 0.05, 0.02), (cx, cy, z + h + 0.002), M['soil'])
    area = max(x1 - x0, y1 - y0)
    for i in range(int(area * 46)):
        px, py = rnd.uniform(x0 + 0.05, x1 - 0.05), rnd.uniform(y0 + 0.05, y1 - 0.05)
        mb.leaf((px, py, z + h), rnd.uniform(0, 2 * pi), radians(rnd.uniform(48, 86)), rnd.uniform(0.5, 1.0) * tall,
                rnd.uniform(0.05, 0.11), rnd.choice(greens), droop=rnd.uniform(0.0, 0.25))
    o = mb.obj()
    return o

def curtain(x0, x1, y, z0, z1, mat):
    mb = MB('zaves')
    n = 14
    prev = None
    for i in range(n + 1):
        t = i / n
        x = x0 + (x1 - x0) * t
        yy = y - 0.035 * (1 + sin(t * pi * 5.0)) / 2 - 0.01
        a, b = mb.bm.verts.new((x, yy, z0)), mb.bm.verts.new((x, yy, z1))
        if prev:
            f = mb.bm.faces.new((prev[0], a, b, prev[1]))
            f.smooth = True
        prev = (a, b)
    mb.mats.append(mat)
    mb.obj()

# ---------------------------------------------------------------- miestnosť
def build_room():
    mb = MB('zaklad')
    mb.box((RX + WT, RY + WT, 0.28), ((RX - WT) / 2, (RY + WT) / 2, -0.16), M['base'])
    mb.obj()
    mb = MB('podlaha')
    mb.box((RX, RY, 0.02), (RX / 2, RY / 2, -0.01), M['floor'])
    mb.obj()

    yw = RY + WT / 2
    wins = [(2.15, 3.65), (4.15, 5.65), (6.15, 7.65)]
    SILL, WTOP = 0.8, 2.25
    mb = MB('stena_sever')
    mb.box((RX + WT, WT, SILL), ((RX - WT) / 2, yw, SILL / 2), M['wall'])
    mb.box((RX + WT, WT, WH - WTOP), ((RX - WT) / 2, yw, (WH + WTOP) / 2), M['wall'])
    piers = [(-WT, wins[0][0])] + [(wins[i][1], wins[i + 1][0]) for i in range(2)] + [(wins[2][1], RX)]
    for a, b in piers:
        mb.box((b - a, WT, WTOP - SILL), ((a + b) / 2, yw, (SILL + WTOP) / 2), M['wall'])
    mb.obj()

    mb = MB('stena_zapad')
    xw = -WT / 2
    D0, D1, DH = 0.45, 1.45, 2.1
    mb.box((WT, D0, WH), (xw, D0 / 2, WH / 2), M['wall'])
    mb.box((WT, RY - D1, WH), (xw, (RY + D1) / 2, WH / 2), M['wall'])
    mb.box((WT, D1 - D0, WH - DH), (xw, (D0 + D1) / 2, (WH + DH) / 2), M['wall'])
    mb.obj()

    # obloženie a lišta
    mb = MB('oblozenie')
    mb.box((RX, 0.025, SILL), (RX / 2, RY - 0.0125, SILL / 2), M['wains'])
    mb.box((0.025, RY - D1 - 0.03, SILL), (0.0125, (RY - 0.03 + D1) / 2, SILL / 2), M['wains'])
    mb.box((0.025, D0, SILL), (0.0125, D0 / 2, SILL / 2), M['wains'])
    mb.box((RX, 0.05, 0.035), (RX / 2, RY - 0.025, SILL + 0.0175), M['walnut'])
    mb.box((0.05, RY - D1 - 0.06, 0.035), (0.025, (RY - 0.06 + D1) / 2, SILL + 0.0175), M['walnut'])
    mb.obj()

    # okná
    mb = MB('okna')
    for a, b in wins:
        cx = (a + b) / 2
        w = b - a
        hh = WTOP - SILL
        cz = (WTOP + SILL) / 2
        mb.box((w, 0.012, hh), (cx, RY + 0.11, cz), M['pane'])
        for xx in (a + 0.025, b - 0.025, cx):
            mb.box((0.05, 0.06, hh), (xx, RY + 0.11, cz), M['black'])
        for zz in (SILL + 0.025, WTOP - 0.025, SILL + hh * 0.62):
            mb.box((w, 0.06, 0.05), (cx, RY + 0.11, zz), M['black'])
        mb.box((w + 0.1, 0.2, 0.04), (cx, RY + 0.03, SILL + 0.045), M['oak'])
    mb.obj()
    for a, b in wins:
        curtain(a - 0.1, a + 0.22, RY - 0.03, SILL + 0.07, WTOP + 0.12, M['linen'])
        curtain(b - 0.22, b + 0.1, RY - 0.03, SILL + 0.07, WTOP + 0.12, M['linen'])
    mb = MB('garniza')
    mb.cyl(0.012, 5.9, (4.9, RY - 0.07, WTOP + 0.13), M['brass'], segs=8, rot=Matrix.Rotation(pi / 2, 4, 'Y'))
    mb.obj()
    # súmrak za oknami (svieti dnu chladným svetlom)
    top = 2.32 if VIEW == 'main' else 2.6
    mb = MB('sumrak')
    mb.poly([(1.5, RY + 0.2, 0.15), (8.3, RY + 0.2, 0.15), (8.3, RY + 0.2, top), (1.5, RY + 0.2, top)], M['dusk'])
    mb.obj()

    # dvere
    mb = MB('dvere')
    yc = (D0 + D1) / 2
    mb.box((0.05, D1 - D0 - 0.04, DH - 0.02), (-0.12, yc, (DH - 0.02) / 2), M['walnut'])
    mb.box((0.012, 0.62, 1.15), (-0.09, yc, 1.3), M['pane'])
    mb.box((0.03, 0.03, 0.22), (-0.07, D0 + 0.12, 1.02), M['brass'])
    mb.box((0.02, 1.1, 0.6), (-0.2, yc, 1.3), M['dusk'])
    mb.obj(bevel=0.006)
    mb = MB('rohoz')
    mb.box((0.95, 1.25, 0.012), (0.62, yc, 0.007), M['rug3'])
    mb.box((0.75, 1.05, 0.004), (0.62, yc, 0.015), M['rug2'])
    mb.obj()

def build_booths():
    ycs = [2.85, 4.65, 6.45]
    mb = MB('boxy')
    for yp in (1.95, 3.75, 5.55, 7.35):
        mb.box((1.42, 0.12, 0.46), (0.77, yp, 0.23), M['walnut'])
        mb.box((1.42, 0.15, 0.56), (0.77, yp, 0.74), M['velvet'])
        mb.box((1.46, 0.18, 0.035), (0.77, yp, 1.04), M['walnut'])
    for yc in ycs:
        for s in (-1, 1):
            ys = yc + s * 0.6
            mb.box((1.40, 0.47, 0.36), (0.77, ys, 0.18), M['walnut'])
            mb.box((1.41, 0.49, 0.1), (0.77, ys, 0.41), M['velvet'])
    mb.obj(bevel=0.012)
    arts = [('art1', 'art2'), ('art4', 'art3'), ('art2', 'art1')]
    for i, yc in enumerate(ycs):
        table_rect(i + 1, 4, 'box', 'v boxe pri stene', 0.85, yc, 1.15, 0.7, {}, legs='ped', top='oak',
                   napkin='ochre', tvar='box',
                   plates=[(0.57, yc - 0.17, 0, 1), (1.13, yc - 0.17, 0, 1), (0.57, yc + 0.17, 0, -1), (1.13, yc + 0.17, 0, -1)])
        pendant(0.85, yc, 1.7, style=0)
        mb = MB('obraz')
        mb.box((0.03, 0.74, 0.54), (0.02, yc, 1.72), M['walnut'])
        mb.box((0.012, 0.64, 0.44), (0.04, yc, 1.72), M[arts[i][1]])
        mb.box((0.012, 0.3, 0.44), (0.046, yc - 0.17, 1.72), M[arts[i][0]])
        mb.cyl(0.11, 0.012, (0.052, yc + 0.12, 1.78), M['art3' if i != 1 else 'art1'], segs=24,
               rot=Matrix.Rotation(pi / 2, 4, 'Y'))
        mb.obj()

def build_bar():
    x0, x1 = 8.0, 10.65
    cx = (x0 + x1) / 2
    mb = MB('bar')
    mb.box((x1 - x0, 0.55, 1.05), (cx, 6.52, 0.525), M['tile'])
    mb.box((x1 - x0 + 0.1, 0.72, 0.05), (cx, 6.5, 1.075), M['walnut'])
    mb.cyl(0.018, x1 - x0 - 0.1, (cx, 6.16, 0.2), M['brass'], segs=10, rot=Matrix.Rotation(pi / 2, 4, 'Y'))
    for xx in (x0 + 0.15, cx, x1 - 0.15):
        mb.box((0.02, 0.1, 0.02), (xx, 6.2, 0.2), M['brass'])
    # zadný pult a police
    mb.box((x1 - x0, 0.42, 0.9), (cx, 7.28, 0.45), M['walnut'])
    mb.box((x1 - x0 + 0.04, 0.46, 0.035), (cx, 7.27, 0.9175), M['oak'])
    for zz in (1.38, 1.8):
        mb.box((x1 - x0 - 0.2, 0.2, 0.035), (cx, 7.39, zz), M['walnut'])
        mb.box((x1 - x0 - 0.3, 0.02, 0.012), (cx, 7.32, zz - 0.026), M['led'])
    # kávovar, pípa, poháre
    mb.box((0.55, 0.36, 0.38), (x0 + 0.5, 7.26, 1.125), M['chrome'])
    mb.box((0.57, 0.38, 0.04), (x0 + 0.5, 7.26, 1.335), M['black'])
    mb.cyl(0.03, 0.34, (9.95, 6.56, 1.27), M['brass'], segs=12)
    mb.box((0.34, 0.05, 0.05), (9.95, 6.56, 1.42), M['brass'])
    for i in range(6):
        mb.cyl(0.03, 0.1, (8.45 + (i % 3) * 0.085, 6.6 + (i // 3) * 0.085, 1.15), M['glass'], segs=10)
    mb.obj(bevel=0.008)
    rnd = random.Random(5)
    mb = MB('flase')
    for zz in (0.935, 1.3975, 1.8175):
        x = x0 + (1.0 if zz < 1.0 else 0.25)
        while x < x1 - 0.2:
            h = rnd.uniform(0.2, 0.3)
            r = rnd.uniform(0.03, 0.042)
            mat = M['btl%d' % rnd.randrange(6)]
            mb.cyl(r, h, (x, 7.4, zz + h / 2), mat, segs=10)
            mb.cyl(r * 0.4, 0.09, (x, 7.4, zz + h + 0.04), mat, segs=8)
            x += r * 2 + rnd.uniform(0.03, 0.1)
    mb.obj()
    for i, xx in enumerate((8.4, 9.1, 9.8, 10.45)):
        seat('s', xx, 5.9, xx, 6.5)
    for xx in (8.65, 9.35, 10.05):
        pendant(xx, 6.5, 1.8, style=0, power=22.0, r=0.13)
    # nápis nad barom
    cu = bpy.data.curves.new('napis', 'FONT')
    cu.body = 'Kôrka'
    for f in ('C:/Windows/Fonts/segoescb.ttf', 'C:/Windows/Fonts/georgiaz.ttf'):
        try:
            cu.font = bpy.data.fonts.load(f)
            break
        except Exception:
            pass
    cu.size = 0.5
    cu.extrude = 0.012
    cu.bevel_depth = 0.006
    cu.align_x = 'CENTER'
    o = bpy.data.objects.new('napis', cu)
    COL.objects.link(o)
    o.location = (cx, RY - 0.03, 2.06)
    o.rotation_euler = (pi / 2, 0, 0)
    cu.materials.append(M['neon'])
    # tabuľa s ponukou pri vchode
    mb = MB('tabula')
    mb.box((0.03, 0.36, 0.8), (0.02, 1.7, 1.55), M['walnut'])
    mb.box((0.012, 0.3, 0.72), (0.04, 1.7, 1.55), M['chalk'])
    for i in range(6):
        mb.box((0.004, 0.2 - (i % 3) * 0.04, 0.02), (0.048, 1.7 - (i % 3) * 0.015, 1.8 - i * 0.09), M['linen'])
    mb.obj()

def build_hall():
    # pri okne
    table_rect(4, 2, 'okno', 'pri okne', 2.9, 7.1, 0.7, 0.7, {'E': 1, 'W': 1}, legs='ped', chair='b', napkin='velvet')
    table_rect(5, 4, 'okno', 'pri okne', 4.9, 6.9, 0.8, 1.1, {'E': 2, 'W': 2}, chair='a', napkin='ochre')
    table_rect(6, 2, 'okno', 'pri okne', 6.9, 7.1, 0.7, 0.7, {'E': 1, 'W': 1}, legs='ped', chair='b', napkin='velvet')
    for i, (x, y) in enumerate(((2.9, 7.1), (4.9, 6.9), (6.9, 7.1))):
        pendant(x, y, 1.72, style=2 if i != 1 else 0)
    # vysoké stoly pri bare
    table_round(7, 2, 'bar', 'vysoký stôl pri bare', 8.4, 4.7, 0.36, 2, h=1.05, top='oakdark', chair='s2', kind='stool', tvar='vysoký')
    table_round(8, 2, 'bar', 'vysoký stôl pri bare', 9.95, 4.7, 0.36, 2, h=1.05, top='oakdark', chair='s2', kind='stool', tvar='vysoký')
    pendant(8.4, 4.7, 1.95, style=1, power=45)
    pendant(9.95, 4.7, 1.95, style=1, power=45)
    # dlhý stôl
    table_rect(9, 8, 'sala', 'dlhý stôl v strede sály', 4.6, 4.7, 2.5, 0.9, {'N': 4, 'S': 4}, chair='c', napkin='terra',
               runner=True, tvar='dlhý')
    for x in (3.8, 4.6, 5.4):
        pendant(x, 4.7, 1.75, style=0, power=45, r=0.17)
    # okrúhle
    table_round(10, 6, 'sala', 'okrúhly stôl v sále', 3.1, 2.05, 0.7, 6, chair='a', napkin='ochre', a0=radians(30))
    pendant(3.1, 2.05, 1.75, style=2, power=70, r=0.26)
    table_round(11, 4, 'sala', 'okrúhly stôl v sále', 5.95, 2.5, 0.5, 4, chair='b', napkin='velvet', a0=radians(45))
    pendant(5.95, 2.5, 1.75, style=3)
    table_rect(12, 4, 'sala', 'v sále neďaleko terasy', 8.25, 2.55, 1.2, 0.8, {'N': 2, 'S': 2}, chair='a', napkin='ochre')
    pendant(8.25, 2.55, 1.75, style=0)
    table_rect(13, 2, 'vpredu', 'v prednej časti sály', 5.2, 0.72, 0.7, 0.7, {'E': 1, 'W': 1}, legs='ped', chair='c', napkin='terra')
    table_rect(14, 2, 'vpredu', 'v prednej časti sály', 7.4, 0.72, 0.7, 0.7, {'E': 1, 'W': 1}, legs='ped', chair='c', napkin='terra')
    pendant(5.2, 0.72, 1.75, style=1)
    pendant(7.4, 0.72, 1.75, style=1)
    # koberce (každá vrstva o kúsok vyššie, aby sa plochy neprekrývali v jednej rovine)
    mb = MB('koberce')
    mb.box((3.7, 2.5, 0.01), (4.6, 4.7, 0.006), M['rug1'])
    mb.box((3.4, 2.2, 0.004), (4.6, 4.7, 0.013), M['rug2'])
    mb.box((3.15, 1.95, 0.004), (4.6, 4.7, 0.017), M['rug1'])
    mb.cyl(1.5, 0.01, (3.1, 2.05, 0.006), M['rug3'], segs=48)
    mb.cyl(1.32, 0.004, (3.1, 2.05, 0.013), M['rug2'], segs=48)
    mb.cyl(1.2, 0.004, (3.1, 2.05, 0.017), M['rug3'], segs=48)
    mb.obj()
    # zeleň a drobnosti
    plant(0.38, 0.24, 'fig', height=1.75, seed=1)
    plant(1.85, 7.15, 'palm', height=1.35, pot='potdark', seed=2, n=22)
    plant(10.45, 3.45, 'fig', height=1.6, pot='potdark', seed=3)
    plant(7.6, 6.05, 'palm', height=1.1, pot='pot', pot_r=0.16, pot_h=0.3, seed=4, n=18)
    planter(10.44, 0.22, 10.72, 1.95, h=0.5, seed=7, tall=0.5)
    for x in (3.9, 5.9):
        mb = MB('policka')
        mb.box((0.3, 0.16, 0.025), (x, RY - 0.08, 1.75), M['walnut'])
        mb.obj()
        plant(x, RY - 0.09, 'trail', z=1.7625, pot_r=0.085, pot_h=0.13, pot='pot', n=20, seed=int(x * 3))
    # kútik na čakanie: pohovka, stolík, stojaca lampa
    mb = MB('pohovka')
    mb.box((0.78, 1.5, 0.2), (9.9, 1.05, 0.2), M['walnut'])
    mb.box((0.62, 1.3, 0.16), (9.82, 1.05, 0.36), M['ochre'])
    mb.box((0.18, 1.5, 0.52), (10.2, 1.05, 0.52), M['ochre'])
    mb.box((0.62, 0.14, 0.34), (9.86, 0.37, 0.45), M['ochre'])
    mb.box((0.62, 0.14, 0.34), (9.86, 1.73, 0.45), M['ochre'])
    mb.box((0.1, 0.36, 0.3), (10.06, 0.7, 0.58), M['velvet'], ry=radians(-14))
    mb.box((0.1, 0.36, 0.3), (10.06, 1.4, 0.58), M['linen'], ry=radians(-14))
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.box((0.05, 0.05, 0.1), (9.9 + sx * 0.32, 1.05 + sy * 0.68, 0.05), M['walnut'])
    mb.obj(bevel=0.03)
    mb = MB('stolik')
    mb.cyl(0.33, 0.035, (8.95, 1.1, 0.42), M['oakdark'], segs=32)
    mb.cyl(0.03, 0.4, (8.95, 1.1, 0.2), M['black'], segs=10)
    mb.cyl(0.2, 0.02, (8.95, 1.1, 0.01), M['black'], segs=20)
    mb.box((0.2, 0.28, 0.02), (8.9, 1.05, 0.4475), M['art2'], rz=0.4)
    mb.cyl(0.035, 0.06, (9.05, 1.2, 0.4675), M['tealight'], segs=12)
    mb.cyl(1.05, 0.01, (9.2, 1.05, 0.006), M['rug2'], segs=40)
    mb.cyl(0.9, 0.004, (9.2, 1.05, 0.013), M['rug1'], segs=40)
    mb.cyl(0.14, 0.02, (9.75, 0.2, 0.01), M['brass'], segs=16)
    mb.cyl(0.012, 1.45, (9.75, 0.2, 0.74), M['brass'], segs=8)
    mb.cyl(0.17, 0.22, (9.75, 0.2, 1.52), M['linen'], r2=0.11, segs=24, caps=False)
    mb.sphere(0.04, (9.75, 0.2, 1.5), M['bulb'], sub=1)
    mb.obj(bevel=0.006)
    point((9.75, 0.2, 1.38), 35)
    # pultík pri vchode
    mb = MB('pultik')
    mb.box((0.55, 0.4, 1.02), (1.75, 0.42, 0.51), M['walnut'])
    mb.box((0.6, 0.45, 0.03), (1.75, 0.42, 1.035), M['oak'])
    mb.box((0.26, 0.2, 0.012), (1.72, 0.42, 1.058), M['linen'], rz=0.2)
    mb.cyl(0.07, 0.02, (1.93, 0.49, 1.06), M['brass'], segs=14)
    mb.cyl(0.012, 0.2, (1.93, 0.49, 1.16), M['brass'], segs=8)
    mb.cyl(0.085, 0.1, (1.93, 0.49, 1.3), M['globe'], r2=0.05, segs=14)
    mb.obj(bevel=0.008)
    point((1.93, 0.49, 1.2), 10)

def build_terrace():
    zt = -0.04
    mb = MB('terasa')
    mb.box((2.8, 4.6, 0.26), (12.2, 2.7, zt - 0.13), M['base'])
    mb.box((2.8, 4.6, 0.02), (12.2, 2.7, zt + 0.0), M['deck'])
    mb.obj()
    zt += 0.01
    table_rect(15, 4, 'terasa', 'na terase', 12.15, 3.55, 0.9, 0.9, {'N': 1, 'S': 1, 'E': 1, 'W': 1}, legs='ped',
               top='oakdark', chair='t', napkin='linen', z0=zt)
    table_round(16, 2, 'terasa', 'na terase', 12.15, 1.65, 0.38, 2, top='oakdark', chair='t', napkin='linen',
                a0=radians(90), z0=zt)
    planter(13.28, 0.5, 13.55, 4.9, h=0.4, z=zt, seed=11, tall=0.42)
    planter(11.2, 0.45, 13.2, 0.7, h=0.4, z=zt, seed=12, tall=0.42)
    planter(11.2, 4.7, 13.2, 4.95, h=0.4, z=zt, seed=13, tall=0.42)
    mb = MB('lampase')
    for (x, y) in ((11.15, 2.7), (13.05, 2.6), (11.1, 4.4)):
        mb.box((0.18, 0.18, 0.03), (x, y, zt + 0.015), M['black'])
        for sx in (-1, 1):
            for sy in (-1, 1):
                mb.box((0.012, 0.012, 0.3), (x + sx * 0.08, y + sy * 0.08, zt + 0.17), M['black'])
        mb.box((0.19, 0.19, 0.025), (x, y, zt + 0.33), M['black'])
        mb.cyl(0.045, 0.14, (x, y, zt + 0.1), M['tealight'], segs=10)
        point((x, y, zt + 0.42), 14)
    mb.obj()
    point((12.15, 2.6, 2.0), 110, size=0.3)

def build_hero_shell():
    mb = MB('strop')
    mb.box((RX + WT, RY + WT, 0.1), ((RX - WT) / 2, (RY + WT) / 2, WH + 0.05), M['ceiling'])
    for y in (1.3, 3.25, 5.2, 7.15):
        mb.box((RX, 0.14, 0.18), (RX / 2, y, WH - 0.09), M['walnut'])
    mb.box((RX, 0.1, WH), (RX / 2, -0.05, WH / 2), M['wall'])
    mb.box((0.1, 2.3, WH), (RX + 0.05, 6.35, WH / 2), M['wall'])
    mb.obj()

mk and chairs_init()
build_room()
build_booths()
build_bar()
build_hall()
build_terrace()
if VIEW == 'hero':
    build_hero_shell()

# ---------------------------------------------------------------- svetlo a svet
world = bpy.data.worlds.new('svet')
try:
    world.use_nodes = True
except Exception:
    pass
scene.world = world
bg = world.node_tree.nodes.get('Background')
if bg is None:
    world.node_tree.nodes.clear()
    bg = world.node_tree.nodes.new('ShaderNodeBackground')
    wo = world.node_tree.nodes.new('ShaderNodeOutputWorld')
    world.node_tree.links.new(bg.outputs[0], wo.inputs[0])
bg.inputs[0].default_value = lin('#6F7FA3') if VIEW == 'main' else lin('#3A3F55')
bg.inputs[1].default_value = float(arg('--world', '0.4' if VIEW == 'main' else '0.25'))

if VIEW == 'main':
    sun = bpy.data.lights.new('fill', 'SUN')
    sun.energy = float(arg('--sun', '1.2'))
    sun.color = (1.0, 0.9, 0.78)
    sun.angle = radians(35)
    so = bpy.data.objects.new('fill', sun)
    so.rotation_euler = Vector((0.45, -0.3, -1.0)).normalized().to_track_quat('-Z', 'Y').to_euler()
    COL.objects.link(so)
else:
    al = bpy.data.lights.new('fill', 'AREA')
    al.energy = float(arg('--fill', '120'))
    al.color = (1.0, 0.8, 0.6)
    al.size = 4.0
    ao = bpy.data.objects.new('fill', al)
    ao.location = (7.5, 2.5, 2.4)
    COL.objects.link(ao)

# ---------------------------------------------------------------- kamera
cam_d = bpy.data.cameras.new('kamera')
cam = bpy.data.objects.new('kamera', cam_d)
COL.objects.link(cam)
scene.camera = cam
scene.render.resolution_x = RES
scene.render.resolution_y = round(RES * ASPECT)
scene.render.resolution_percentage = 100

def look_at(o, pos, target):
    o.location = pos
    o.rotation_euler = (Vector(target) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()

if VIEW == 'main':
    az, el, dist = radians(float(arg('--az', '36'))), radians(float(arg('--el', '37'))), 70.0
    target = Vector((6.4, 3.75, 0.9))
    pos = target + dist * Vector((sin(az) * cos(el), -cos(az) * cos(el), sin(el)))
    look_at(cam, pos, target)
    cam_d.lens = 200
    cam_d.clip_end = 300
    bpy.context.view_layer.update()
    pts = []
    for o in COL.objects:
        if o.type in ('MESH', 'FONT'):
            for c in o.bound_box:
                pts.append(o.matrix_world @ Vector(c))
    pts.append(Vector((0, RY, WH + 0.05)))
    W, H = scene.render.resolution_x, scene.render.resolution_y
    for it in range(10):
        bpy.context.view_layer.update()
        cs = [world_to_camera_view(scene, cam, p) for p in pts]
        minx, maxx = min(c.x for c in cs), max(c.x for c in cs)
        miny, maxy = min(c.y for c in cs), max(c.y for c in cs)
        cx, cy = (minx + maxx) / 2, (miny + maxy) / 2
        vw = dist * cam_d.sensor_width / cam_d.lens
        mw = cam.matrix_world.to_3x3()
        cam.location += (mw @ Vector((1, 0, 0))) * (cx - 0.5) * vw + (mw @ Vector((0, 1, 0))) * (cy - 0.5) * vw * H / W
        cam_d.lens *= 0.955 / max(maxx - minx, maxy - miny)
    bpy.context.view_layer.update()
else:
    look_at(cam, (float(arg('--kx', '8.6')), float(arg('--ky', '1.7')), float(arg('--kz', '1.2'))),
            (float(arg('--ax', '4.0')), float(arg('--ay', '6.2')), float(arg('--az2', '0.95'))))
    cam_d.lens = float(arg('--ohnisko', '28'))
    cam_d.dof.use_dof = True
    cam_d.dof.focus_distance = float(arg('--ostrenie', '3.6'))
    cam_d.dof.aperture_fstop = float(arg('--fstop', '2.0'))
    bpy.context.view_layer.update()

# ---------------------------------------------------------------- polohy stolov do JSON
if VIEW == 'main' and JSON_OUT:
    def pct(v):
        c = world_to_camera_view(scene, cam, v)
        return [round(c.x * 100, 2), round((1 - c.y) * 100, 2)]
    data = dict(obrazok=dict(w=1600, h=1100), stoly=[])
    for t in sorted(TABLES, key=lambda t: t['id']):
        c = pct(t['c'])
        data['stoly'].append(dict(id=t['id'], miest=t['seats'], zona=t['zone'], kde=t['kde'], tvar=t['tvar'],
                                  x=c[0], y=c[1], obrys=[pct(p) for p in t['pts']]))
    jp = os.path.abspath(JSON_OUT)
    with open(jp, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    with open(os.path.splitext(jp)[0] + '.js', 'w', encoding='utf-8') as f:
        f.write('// Vygenerované skriptom blender/scena.py (world_to_camera_view). Needitovať ručne.\n')
        f.write('window.KORKA_STOLY = ' + json.dumps(data, ensure_ascii=False) + ';\n')
    print('JSON', jp, len(data['stoly']), 'stolov')

# ---------------------------------------------------------------- render
scene.render.engine = 'CYCLES'
cy = scene.cycles
cy.device = 'CPU'
cy.samples = SAMPLES
cy.use_adaptive_sampling = True
cy.adaptive_threshold = 0.03
cy.use_denoising = True
try:
    cy.denoiser = 'OPENIMAGEDENOISE'
    cy.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
except Exception as e:
    print('denoiser', e)
cy.max_bounces = 6
cy.diffuse_bounces = 3
cy.glossy_bounces = 3
cy.transmission_bounces = 6
cy.transparent_max_bounces = 6
cy.caustics_reflective = False
cy.caustics_refractive = False
cy.sample_clamp_indirect = 6.0
scene.render.film_transparent = (VIEW == 'main')
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA' if VIEW == 'main' else 'RGB'
scene.view_settings.view_transform = 'AgX'
for look in (arg('--look', 'AgX - Medium High Contrast'), 'Medium High Contrast'):
    try:
        scene.view_settings.look = look
        break
    except Exception:
        pass
scene.view_settings.exposure = float(arg('--exposure', '0.0'))
scene.render.filepath = OUT
if '--norender' not in argv:
    bpy.ops.render.render(write_still=True)
    print('RENDER', OUT)
