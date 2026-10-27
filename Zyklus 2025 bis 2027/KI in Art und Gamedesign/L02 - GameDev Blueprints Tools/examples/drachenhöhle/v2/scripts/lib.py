"""Shared helpers for the hospital corridor build: primitives, collections and
procedural materials. Everything is generated from scratch (no external assets)."""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Euler

PI = math.pi
D2R = PI / 180.0


# ----------------------------------------------------------------------------
# Collections / objects
# ----------------------------------------------------------------------------
def get_coll(name, parent=None):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(c)
    return c


def new_obj(name, data, col, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), parent=None):
    o = bpy.data.objects.new(name, data)
    col.objects.link(o)
    o.location = loc
    o.rotation_euler = rot
    o.scale = scale
    if parent is not None:
        o.parent = parent
    return o


def empty(name, col, loc=(0, 0, 0), rot=(0, 0, 0), parent=None):
    o = new_obj(name, None, col, loc, rot, parent=parent)
    o.empty_display_size = 0.25
    return o


def instance(name, src_coll, col, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1)):
    """Collection instance (keeps memory low and lets props be edited in one place)."""
    o = new_obj(name, None, col, loc, rot, scale)
    o.instance_type = 'COLLECTION'
    o.instance_collection = src_coll
    o.empty_display_size = 0.3
    return o


def _finish(bm, name, col, mat, loc, rot, smooth, sharp, parent):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    mats = mat if isinstance(mat, (list, tuple)) else [mat]
    for m in mats:
        if m is not None:
            me.materials.append(m)
    if smooth:
        me.shade_smooth()
        if sharp is not None:
            me.set_sharp_from_angle(angle=sharp)
    return new_obj(name, me, col, loc, rot, parent=parent)


def add_bevel(o, width, segs=2):
    m = o.modifiers.new('Bevel', 'BEVEL')
    m.width = width
    m.segments = segs
    m.limit_method = 'ANGLE'
    m.angle_limit = 50 * D2R
    m.harden_normals = True
    if o.type == 'MESH':
        o.data.shade_smooth()
    return m


def box(name, size, loc, mat, col, rot=(0, 0, 0), bevel=0.0, segs=2, parent=None, base=False):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    sx, sy, sz = size
    for v in bm.verts:
        v.co = Vector((v.co.x * sx, v.co.y * sy, v.co.z * sz + (sz / 2 if base else 0)))
    o = _finish(bm, name, col, mat, loc, rot, False, None, parent)
    if bevel > 0:
        add_bevel(o, min(bevel, min(size) * 0.45), segs)
    return o


def box_minmax(name, mn, mx, mat, col, bevel=0.0, segs=2, parent=None):
    size = [mx[i] - mn[i] for i in range(3)]
    loc = [(mx[i] + mn[i]) / 2 for i in range(3)]
    return box(name, size, loc, mat, col, bevel=bevel, segs=segs, parent=parent)


def cyl(name, r, h, loc, mat, col, rot=(0, 0, 0), seg=24, r2=None, cap=True, smooth=True,
        bevel=0.0, parent=None, base=False):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=cap, cap_tris=False, segments=seg, radius1=r,
                          radius2=r if r2 is None else r2, depth=h)
    if base:
        for v in bm.verts:
            v.co.z += h / 2
    o = _finish(bm, name, col, mat, loc, rot, smooth, 40 * D2R, parent)
    if bevel > 0:
        add_bevel(o, bevel, 2)
    return o


def sphere(name, r, loc, mat, col, scale=(1, 1, 1), seg=24, rings=12, rot=(0, 0, 0), parent=None):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=r)
    for v in bm.verts:
        v.co = Vector((v.co.x * scale[0], v.co.y * scale[1], v.co.z * scale[2]))
    return _finish(bm, name, col, mat, loc, rot, True, None, parent)


def torus(name, R, r, loc, mat, col, rot=(0, 0, 0), seg=32, rseg=10, parent=None):
    bm = bmesh.new()
    rings = []
    for i in range(seg):
        a = 2 * PI * i / seg
        ring = []
        for j in range(rseg):
            b = 2 * PI * j / rseg
            ring.append(bm.verts.new(((R + r * math.cos(b)) * math.cos(a),
                                      (R + r * math.cos(b)) * math.sin(a), r * math.sin(b))))
        rings.append(ring)
    for i in range(seg):
        for j in range(rseg):
            bm.faces.new((rings[i][j], rings[(i + 1) % seg][j],
                          rings[(i + 1) % seg][(j + 1) % rseg], rings[i][(j + 1) % rseg]))
    return _finish(bm, name, col, mat, loc, rot, True, None, parent)


def round_corners(pts, radius, steps=4):
    """Fillet the corners of a polyline so curve tubes bend like real tubing."""
    if len(pts) < 3 or radius <= 0:
        return pts
    P = [Vector(p) for p in pts]
    out = [P[0]]
    for i in range(1, len(P) - 1):
        a, b, c = P[i - 1], P[i], P[i + 1]
        d1, d2 = (a - b), (c - b)
        l1, l2 = d1.length, d2.length
        if l1 < 1e-6 or l2 < 1e-6:
            continue
        rr = min(radius, l1 * 0.45, l2 * 0.45)
        p1 = b + d1.normalized() * rr
        p2 = b + d2.normalized() * rr
        for s in range(steps + 1):
            t = s / steps
            q = (1 - t) ** 2 * p1 + 2 * (1 - t) * t * b + t ** 2 * p2
            out.append(q)
    out.append(P[-1])
    return [tuple(p) for p in out]


def tube(name, pts, r, mat, col, loc=(0, 0, 0), rot=(0, 0, 0), fillet=0.0, cyclic=False,
         parent=None, res=3):
    if fillet > 0:
        pts = round_corners(pts, fillet)
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_mode = 'ROUND'
    cu.bevel_depth = r
    cu.bevel_resolution = res
    cu.use_fill_caps = True
    sp = cu.splines.new('POLY')
    sp.points.add(len(pts) - 1)
    for p, c in zip(sp.points, pts):
        p.co = (c[0], c[1], c[2], 1.0)
    sp.use_cyclic_u = cyclic
    sp.use_smooth = True
    if mat is not None:
        cu.materials.append(mat)
    return new_obj(name, cu, col, loc, rot, parent=parent)


def text(name, body, size, loc, rot, mat, col, align_x='CENTER', align_y='CENTER', extrude=0.0,
         parent=None, spacing=1.0):
    cu = bpy.data.curves.new(name, 'FONT')
    cu.body = body
    cu.size = size
    cu.align_x = align_x
    cu.align_y = align_y
    cu.extrude = extrude
    cu.space_character = spacing
    if mat is not None:
        cu.materials.append(mat)
    return new_obj(name, cu, col, loc, rot, parent=parent)


def panel_grid(name, nx, ny, size, mat, col, loc, rot=(0, 0, 0), parent=None):
    """Subdivided plane (used for curtains / cloth that we deform procedurally)."""
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=nx, y_segments=ny, size=0.5)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], 0))
    return _finish(bm, name, col, mat, loc, rot, True, None, parent)


# ----------------------------------------------------------------------------
# Node helpers
# ----------------------------------------------------------------------------
class NB:
    def __init__(self, mat):
        if mat.node_tree is None:
            mat.use_nodes = True
        self.nt = mat.node_tree
        self.nodes = self.nt.nodes
        self.links = self.nt.links
        self.bsdf = self.nodes.get('Principled BSDF')
        self.out = self.nodes.get('Material Output')
        self._x = -300

    def n(self, kind, **kw):
        nd = self.nodes.new(kind)
        nd.location = (self._x, random.uniform(-400, 400))
        self._x -= 40
        for k, v in kw.items():
            if k in nd.inputs:
                nd.inputs[k].default_value = v
            else:
                setattr(nd, k, v)
        return nd

    def l(self, a, b):
        self.links.new(a, b)

    def sock(self, node, ident, out=False):
        for s in (node.outputs if out else node.inputs):
            if s.identifier == ident:
                return s
        raise KeyError(ident)

    def mix(self, fac, a, b, blend='MIX'):
        m = self.n('ShaderNodeMix', data_type='RGBA', blend_type=blend)
        for val, ident in ((fac, 'Factor_Float'), (a, 'A_Color'), (b, 'B_Color')):
            s = self.sock(m, ident)
            if isinstance(val, bpy.types.NodeSocket):
                self.l(val, s)
            else:
                s.default_value = (*val, 1.0) if isinstance(val, tuple) and len(val) == 3 else val
        return self.sock(m, 'Result_Color', out=True)

    def ramp(self, src, stops, interp='LINEAR'):
        r = self.n('ShaderNodeValToRGB')
        r.color_ramp.interpolation = interp
        el = r.color_ramp.elements
        while len(el) > 2:
            el.remove(el[-1])
        for i, (pos, col) in enumerate(stops):
            e = el[i] if i < 2 else el.new(pos)
            e.position = pos
            e.color = col if len(col) == 4 else (*col, 1.0)
        self.l(src, r.inputs['Fac'])
        return r.outputs['Color']

    def maprange(self, src, a, b, c, d):
        m = self.n('ShaderNodeMapRange')
        m.inputs['From Min'].default_value = a
        m.inputs['From Max'].default_value = b
        m.inputs['To Min'].default_value = c
        m.inputs['To Max'].default_value = d
        self.l(src, m.inputs['Value'])
        return m.outputs['Result']

    def math(self, op, a, b=0.0):
        m = self.n('ShaderNodeMath', operation=op)
        for i, v in enumerate((a, b)):
            if isinstance(v, bpy.types.NodeSocket):
                self.l(v, m.inputs[i])
            else:
                m.inputs[i].default_value = v
        return m.outputs[0]

    def coords(self, scale=(1, 1, 1), loc=(0, 0, 0), kind='Object'):
        if kind == 'Position':
            src = self.n('ShaderNodeNewGeometry').outputs['Position']
        else:
            src = self.n('ShaderNodeTexCoord').outputs[kind]
        mp = self.n('ShaderNodeMapping')
        mp.inputs['Scale'].default_value = scale
        mp.inputs['Location'].default_value = loc
        self.l(src, mp.inputs['Vector'])
        return mp.outputs['Vector']

    def noise(self, vec, scale, detail=2.0, rough=0.5, distortion=0.0):
        t = self.n('ShaderNodeTexNoise')
        t.inputs['Scale'].default_value = scale
        t.inputs['Detail'].default_value = detail
        t.inputs['Roughness'].default_value = rough
        t.inputs['Distortion'].default_value = distortion
        if vec is not None:
            self.l(vec, t.inputs['Vector'])
        return t

    def bump(self, height, strength, distance=0.01, normal=None):
        b = self.n('ShaderNodeBump')
        b.inputs['Strength'].default_value = strength
        b.inputs['Distance'].default_value = distance
        self.l(height, b.inputs['Height'])
        if normal is not None:
            self.l(normal, b.inputs['Normal'])
        return b.outputs['Normal']

    def set(self, **kw):
        for k, v in kw.items():
            k = k.replace('_', ' ')
            if isinstance(v, bpy.types.NodeSocket):
                self.l(v, self.bsdf.inputs[k])
            else:
                self.bsdf.inputs[k].default_value = v


def new_mat(name):
    m = bpy.data.materials.get(name)
    if m is not None:
        bpy.data.materials.remove(m)
    m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:
        pass
    return m, NB(m)


def rgba(c):
    return (*c, 1.0) if len(c) == 3 else c


# ----------------------------------------------------------------------------
# Material library
# ----------------------------------------------------------------------------
_CACHE = {}


def simple(name, color, rough=0.5, metal=0.0, coat=0.0, coat_rough=0.05, sheen=0.0,
           emit=None, emit_strength=0.0, spec=0.5, bump=0.0, bump_scale=200.0):
    m, nb = new_mat(name)
    nb.set(Base_Color=rgba(color), Roughness=rough, Metallic=metal)
    nb.bsdf.inputs['Specular IOR Level'].default_value = spec
    if coat:
        nb.set(Coat_Weight=coat, Coat_Roughness=coat_rough)
    if sheen:
        nb.set(Sheen_Weight=sheen)
    if emit is not None:
        nb.set(Emission_Color=rgba(emit), Emission_Strength=emit_strength)
    if bump:
        v = nb.coords()
        t = nb.noise(v, bump_scale, 2.0)
        nb.set(Normal=nb.bump(t.outputs['Fac'], bump, 0.002))
    m.diffuse_color = rgba(color)
    return m


def mat_floor():
    m, nb = new_mat('Floor_Vinyl')
    v = nb.coords(kind='Position')
    br = nb.n('ShaderNodeTexBrick', offset=0.0, squash=1.0)
    br.inputs['Scale'].default_value = 1.0
    br.inputs['Brick Width'].default_value = 0.6
    br.inputs['Row Height'].default_value = 0.6
    br.inputs['Mortar Size'].default_value = 0.0022
    br.inputs['Mortar Smooth'].default_value = 0.4
    br.inputs['Bias'].default_value = 0.0
    br.inputs['Color1'].default_value = (0.50, 0.53, 0.53, 1)
    br.inputs['Color2'].default_value = (0.57, 0.59, 0.58, 1)
    br.inputs['Mortar'].default_value = (0.36, 0.38, 0.38, 1)
    nb.l(v, br.inputs['Vector'])
    sp = nb.noise(v, 260.0, 1.0)
    speck = nb.ramp(sp.outputs['Fac'], [(0.0, (0.45, 0.48, 0.52)), (0.33, (0.86, 0.87, 0.88)),
                                       (0.67, (1.0, 1.0, 1.0))], 'CONSTANT')
    col = nb.mix(1.0, br.outputs['Color'], speck, 'MULTIPLY')
    big = nb.noise(v, 0.35, 5.0, 0.6)
    grime = nb.ramp(big.outputs['Fac'], [(0.3, (0.82, 0.80, 0.76)), (0.7, (1, 1, 1))])
    col = nb.mix(1.0, col, grime, 'MULTIPLY')
    nb.set(Base_Color=col)
    rn = nb.noise(v, 1.6, 6.0, 0.6)
    rough = nb.maprange(rn.outputs['Fac'], 0.3, 0.7, 0.16, 0.42)
    scuff = nb.noise(nb.coords((0.6, 6.0, 1.0), kind='Position'), 3.0, 4.0)
    rough = nb.math('ADD', rough, nb.maprange(scuff.outputs['Fac'], 0.55, 0.75, 0.0, 0.15))
    rough = nb.math('ADD', rough, nb.math('MULTIPLY', br.outputs['Fac'], 0.4))
    nb.set(Roughness=rough, Coat_Weight=0.6, Coat_Roughness=0.06)
    seam = nb.math('MULTIPLY', br.outputs['Fac'], -1.0)
    fine = nb.noise(v, 90.0, 2.0)
    n1 = nb.bump(fine.outputs['Fac'], 0.05, 0.002)
    nb.set(Normal=nb.bump(seam, 0.35, 0.003, n1))
    m.diffuse_color = (0.5, 0.52, 0.52, 1)
    return m


import os
TEX_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'textures', 'polyhaven')
# Floor look: 'polyhaven' uses the downloaded terrazzo maps, 'procedural' the original vinyl shader
FLOOR_STYLE = 'polyhaven'
FLOOR_TEX = dict(asset='terrazzo_tiles', size_m=2.0, saturation=0.35, value=1.6, tint=(0.93, 0.97, 1.0))


def _tex(nb, vec, path, non_color=False):
    img = bpy.data.images.load(path, check_existing=True)
    if non_color:
        img.colorspace_settings.name = 'Non-Color'
    t = nb.n('ShaderNodeTexImage')
    t.image = img
    t.interpolation = 'Linear'
    nb.l(vec, t.inputs['Vector'])
    return t


def mat_floor_pbr(asset='terrazzo_tiles', size_m=2.0, saturation=1.0, value=1.0, tint=(1, 1, 1)):
    """Poly Haven PBR maps, projected top-down in world space (floor boxes carry no UVs)."""
    import os
    m, nb = new_mat('Floor_Terrazzo_PolyHaven')
    f = lambda key: os.path.join(TEX_DIR, f'{asset}_{key}_2k.jpg')
    v = nb.coords((1.0 / size_m, 1.0 / size_m, 1.0), kind='Position')
    diff = _tex(nb, v, f('Diffuse'))
    hsv = nb.n('ShaderNodeHueSaturation')
    hsv.inputs['Saturation'].default_value = saturation
    hsv.inputs['Value'].default_value = value
    nb.l(diff.outputs['Color'], hsv.inputs['Color'])
    col = nb.mix(1.0, hsv.outputs['Color'], tint, 'MULTIPLY')
    # large-scale tonal breakup hides the 2 m repeat down the long corridor
    big = nb.noise(nb.coords(kind='Position'), 0.3, 5.0, 0.6)
    grime = nb.ramp(big.outputs['Fac'], [(0.3, (0.84, 0.82, 0.79)), (0.7, (1, 1, 1))])
    nb.set(Base_Color=nb.mix(1.0, col, grime, 'MULTIPLY'))
    rough = _tex(nb, v, f('Rough'), True)
    scuff = nb.noise(nb.coords((0.6, 6.0, 1.0), kind='Position'), 3.0, 4.0)
    r = nb.math('ADD', nb.maprange(rough.outputs['Color'], 0.0, 1.0, 0.12, 0.55),
                nb.maprange(scuff.outputs['Fac'], 0.55, 0.75, 0.0, 0.12))
    nb.set(Roughness=r, Coat_Weight=0.45, Coat_Roughness=0.07)
    disp = _tex(nb, v, f('Displacement'), True)
    nb.set(Normal=nb.bump(disp.outputs['Color'], 0.5, 0.004))
    m.diffuse_color = (0.45, 0.42, 0.38, 1)
    return m


def mat_wall(name='Wall_Paint', color=(0.68, 0.67, 0.60)):
    m, nb = new_mat(name)
    v = nb.coords()
    big = nb.noise(v, 1.5, 4.0, 0.55)
    tone = nb.ramp(big.outputs['Fac'], [(0.3, tuple(c * 0.93 for c in color)), (0.7, color)])
    nb.set(Base_Color=tone, Roughness=0.62)
    fine = nb.noise(v, 140.0, 2.0)
    nb.set(Normal=nb.bump(fine.outputs['Fac'], 0.06, 0.002))
    m.diffuse_color = rgba(color)
    return m


def mat_ceiling():
    m, nb = new_mat('Ceiling_Tile')
    v = nb.coords(loc=(0.3, 0.0, 0.0), kind='Position')
    br = nb.n('ShaderNodeTexBrick', offset=0.0, squash=1.0)
    br.inputs['Scale'].default_value = 1.0
    br.inputs['Brick Width'].default_value = 0.6
    br.inputs['Row Height'].default_value = 0.6
    br.inputs['Mortar Size'].default_value = 0.012
    br.inputs['Mortar Smooth'].default_value = 0.1
    br.inputs['Bias'].default_value = 0.0
    br.inputs['Color1'].default_value = (0.80, 0.80, 0.78, 1)
    br.inputs['Color2'].default_value = (0.84, 0.84, 0.82, 1)
    br.inputs['Mortar'].default_value = (0.72, 0.72, 0.71, 1)
    nb.l(v, br.inputs['Vector'])
    pits = nb.n('ShaderNodeTexVoronoi')
    pits.inputs['Scale'].default_value = 160.0
    nb.l(v, pits.inputs['Vector'])
    pit = nb.ramp(pits.outputs['Distance'], [(0.0, (0, 0, 0)), (0.25, (1, 1, 1))])
    col = nb.mix(0.15, br.outputs['Color'], pit, 'MULTIPLY')
    nb.set(Base_Color=col)
    nb.set(Roughness=nb.maprange(br.outputs['Fac'], 0, 1, 0.92, 0.35))
    h = nb.math('ADD', br.outputs['Fac'], nb.math('MULTIPLY', pits.outputs['Distance'], 0.2))
    nb.set(Normal=nb.bump(h, 0.25, 0.003))
    m.diffuse_color = (0.8, 0.8, 0.78, 1)
    return m


def mat_wood(name='Wood_Oak', c1=(0.44, 0.28, 0.14), c2=(0.60, 0.42, 0.24), grain=(40.0, 40.0, 1.2)):
    m, nb = new_mat(name)
    v = nb.coords(grain)
    n1 = nb.noise(v, 1.5, 8.0, 0.65, 0.6)
    w = nb.n('ShaderNodeTexWave', wave_type='RINGS')
    w.inputs['Scale'].default_value = 2.5
    w.inputs['Distortion'].default_value = 8.0
    w.inputs['Detail'].default_value = 4.0
    nb.l(nb.coords(tuple(3.0 if g > 10 else 0.12 for g in grain)), w.inputs['Vector'])
    f = nb.math('ADD', nb.math('MULTIPLY', n1.outputs['Fac'], 0.7), nb.math('MULTIPLY', w.outputs['Fac'], 0.3))
    col = nb.ramp(f, [(0.25, c1), (0.75, c2)])
    nb.set(Base_Color=col, Roughness=nb.maprange(f, 0, 1, 0.5, 0.35), Coat_Weight=0.25,
           Coat_Roughness=0.15)
    nb.set(Normal=nb.bump(n1.outputs['Fac'], 0.08, 0.001))
    m.diffuse_color = rgba(c2)
    return m


def mat_brushed(name='Stainless', color=(0.72, 0.72, 0.73), r0=0.18, r1=0.34):
    m, nb = new_mat(name)
    n1 = nb.noise(nb.coords((1.0, 1.0, 80.0)), 6.0, 4.0)
    nb.set(Base_Color=rgba(color), Metallic=1.0,
           Roughness=nb.maprange(n1.outputs['Fac'], 0.3, 0.7, r0, r1))
    nb.set(Normal=nb.bump(n1.outputs['Fac'], 0.03, 0.001))
    m.diffuse_color = rgba(color)
    return m


def mat_glass(name='Glass', tint=(0.85, 0.92, 0.95), alpha=0.06):
    m, nb = new_mat(name)
    nb.set(Base_Color=rgba(tint), Roughness=0.02, Alpha=alpha, IOR=1.5)
    nb.bsdf.inputs['Specular IOR Level'].default_value = 1.0
    m.surface_render_method = 'DITHERED'
    m.diffuse_color = (*tint, 0.2)
    return m


def mat_emit(name, color, strength):
    m, nb = new_mat(name)
    nb.set(Base_Color=(0, 0, 0, 1), Roughness=0.4, Emission_Color=rgba(color),
           Emission_Strength=strength)
    m.diffuse_color = rgba(color)
    return m


def mat_light_panel(name='Light_Panel', color=(0.90, 0.95, 1.0), strength=9.0):
    m, nb = new_mat(name)
    v = nb.coords()
    br = nb.n('ShaderNodeTexBrick', offset=0.0)
    br.inputs['Scale'].default_value = 1.0
    br.inputs['Brick Width'].default_value = 0.012
    br.inputs['Row Height'].default_value = 0.012
    br.inputs['Mortar Size'].default_value = 0.0015
    nb.l(v, br.inputs['Vector'])
    pat = nb.maprange(br.outputs['Fac'], 0, 1, 1.0, 0.82)
    vign = nb.n('ShaderNodeTexGradient', gradient_type='SPHERICAL')
    nb.l(nb.coords((1.4, 0.8, 1.0)), vign.inputs['Vector'])
    vf = nb.maprange(vign.outputs['Fac'], 0.0, 0.5, 0.8, 1.0)
    s = nb.math('MULTIPLY', nb.math('MULTIPLY', pat, vf), strength)
    nb.set(Base_Color=(0.9, 0.9, 0.9, 1), Roughness=0.3, Emission_Color=rgba(color),
           Emission_Strength=s)
    m.diffuse_color = rgba(color)
    return m


def mat_sky():
    m, nb = new_mat('Sky_Backdrop')
    v = nb.coords(kind='Position')
    sep = nb.n('ShaderNodeSeparateXYZ')
    nb.l(v, sep.inputs['Vector'])
    z = nb.maprange(sep.outputs['Z'], -2.0, 14.0, 0.0, 1.0)
    col = nb.ramp(z, [(0.0, (1.0, 0.40, 0.14)), (0.15, (1.0, 0.58, 0.30)), (0.35, (0.70, 0.56, 0.58)),
                      (0.65, (0.24, 0.30, 0.50)), (1.0, (0.07, 0.10, 0.22))])
    # soft sun bloom low on the horizon, slightly right of the window centre
    g = nb.n('ShaderNodeTexGradient', gradient_type='SPHERICAL')
    sx, sz = 1 / 30.0, 1 / 9.0
    nb.l(nb.coords((sx, 0.0, sz), loc=(-6.0 * sx, 0.0, -1.0 * sz), kind='Position'), g.inputs['Vector'])
    glow = nb.math('POWER', g.outputs['Fac'], 2.5)
    col = nb.mix(glow, col, (1.0, 0.80, 0.55, 1), 'MIX')
    em = nb.n('ShaderNodeEmission')
    nb.l(col, em.inputs['Color'])
    nb.l(nb.math('ADD', 1.6, nb.math('MULTIPLY', glow, 8.0)), em.inputs['Strength'])
    nb.l(em.outputs['Emission'], nb.out.inputs['Surface'])
    nb.nodes.remove(nb.bsdf)
    m.diffuse_color = (1.0, 0.6, 0.3, 1)
    return m


def mat_city(name='City_Silhouette', lit=(1.0, 0.72, 0.42), density=0.3, strength=4.0):
    m, nb = new_mat(name)
    v = nb.coords()
    br = nb.n('ShaderNodeTexBrick', offset=0.0, squash=1.0)
    br.inputs['Scale'].default_value = 1.0
    br.inputs['Brick Width'].default_value = 1.6
    br.inputs['Row Height'].default_value = 1.2
    br.inputs['Mortar Size'].default_value = 0.35
    br.inputs['Mortar Smooth'].default_value = 0.05
    br.inputs['Bias'].default_value = 0.0
    br.inputs['Color1'].default_value = (0, 0, 0, 1)
    br.inputs['Color2'].default_value = (1, 1, 1, 1)
    br.inputs['Mortar'].default_value = (0, 0, 0, 1)
    sep = nb.n('ShaderNodeSeparateXYZ')
    nb.l(v, sep.inputs['Vector'])
    comb = nb.n('ShaderNodeCombineXYZ')
    nb.l(nb.math('ADD', sep.outputs['X'], sep.outputs['Y']), comb.inputs['X'])
    nb.l(sep.outputs['Z'], comb.inputs['Y'])
    nb.l(comb.outputs['Vector'], br.inputs['Vector'])
    on = nb.ramp(br.outputs['Color'], [(1.0 - density, (0, 0, 0)), (1.0 - density + 0.02, (1, 1, 1))],
                 'CONSTANT')
    nb.set(Base_Color=(0.012, 0.014, 0.02, 1), Roughness=0.8, Emission_Color=rgba(lit))
    nb.set(Emission_Strength=nb.math('MULTIPLY', nb.math('MULTIPLY', on, nb.math('SUBTRACT', 1.0, br.outputs['Fac'])), strength))
    m.diffuse_color = (0.02, 0.02, 0.03, 1)
    return m


def mat_screen(name, base=(0.02, 0.05, 0.09), line=(0.2, 1.0, 0.45), strength=3.0, kind='ecg'):
    m, nb = new_mat(name)
    v = nb.coords(kind='Generated')
    sep = nb.n('ShaderNodeSeparateXYZ')
    nb.l(v, sep.inputs['Vector'])
    if kind == 'ecg':
        # three horizontal traces made from sine waves
        w = nb.n('ShaderNodeTexWave', wave_type='BANDS', bands_direction='Z')
        w.inputs['Scale'].default_value = 1.5
        w.inputs['Distortion'].default_value = 3.0
        w.inputs['Detail'].default_value = 0.0
        nb.l(v, w.inputs['Vector'])
        bands = nb.ramp(w.outputs['Fac'], [(0.0, (0, 0, 0)), (0.93, (0, 0, 0)), (0.97, line),
                                          (1.0, (1, 1, 1))])
        col = nb.mix(1.0, base, bands, 'ADD')
    else:
        # generic UI: blocks of light panes
        br = nb.n('ShaderNodeTexBrick', offset=0.0)
        br.inputs['Scale'].default_value = 1.0
        br.inputs['Brick Width'].default_value = 0.33
        br.inputs['Row Height'].default_value = 0.12
        br.inputs['Mortar Size'].default_value = 0.02
        br.inputs['Color1'].default_value = rgba(line)
        br.inputs['Color2'].default_value = (0.9, 0.95, 1.0, 1)
        br.inputs['Mortar'].default_value = rgba(base)
        nb.l(v, br.inputs['Vector'])
        col = br.outputs['Color']
    nb.set(Base_Color=(0.01, 0.01, 0.01, 1), Roughness=0.15, Emission_Color=col,
           Emission_Strength=strength)
    m.diffuse_color = rgba(line)
    return m


def mat_fabric(name, color, sheen=0.5, scale=900.0, rough=0.85, check=None):
    m, nb = new_mat(name)
    v = nb.coords()
    wv = nb.noise(v, scale, 1.0)
    col = rgba(color)
    if check is not None:
        br = nb.n('ShaderNodeTexChecker')
        br.inputs['Scale'].default_value = 12.0
        br.inputs['Color1'].default_value = rgba(color)
        br.inputs['Color2'].default_value = rgba(check)
        nb.l(v, br.inputs['Vector'])
        col = br.outputs['Color']
    nb.set(Base_Color=col, Roughness=rough, Sheen_Weight=sheen, Sheen_Roughness=0.4)
    nb.set(Normal=nb.bump(wv.outputs['Fac'], 0.15, 0.001))
    m.diffuse_color = rgba(color)
    return m


def mat_cork():
    m, nb = new_mat('Cork')
    v = nb.coords()
    n1 = nb.noise(v, 220.0, 3.0, 0.7)
    col = nb.ramp(n1.outputs['Fac'], [(0.3, (0.30, 0.17, 0.08)), (0.5, (0.55, 0.36, 0.18)),
                                     (0.7, (0.68, 0.48, 0.26))])
    nb.set(Base_Color=col, Roughness=0.9)
    nb.set(Normal=nb.bump(n1.outputs['Fac'], 0.4, 0.002))
    m.diffuse_color = (0.55, 0.36, 0.18, 1)
    return m


def build_materials():
    _CACHE.clear()
    M = _CACHE
    M['floor'] = mat_floor_pbr(**FLOOR_TEX) if FLOOR_STYLE == 'polyhaven' else mat_floor()
    M['wall'] = mat_wall()
    M['wall_room'] = mat_wall('Wall_Room', (0.50, 0.58, 0.56))
    M['wall_lower'] = simple('Wall_Protection_PVC', (0.18, 0.32, 0.31), 0.38, coat=0.2, bump=0.08,
                             bump_scale=300)
    M['skirting'] = simple('Rubber_Skirting', (0.04, 0.05, 0.05), 0.55)
    M['ceiling'] = mat_ceiling()
    M['ceiling_plain'] = simple('Ceiling_Plain', (0.78, 0.78, 0.76), 0.9)
    M['handrail'] = mat_wood('Handrail_Wood', (0.45, 0.30, 0.16), (0.66, 0.48, 0.29), grain=(40.0, 1.2, 40.0))
    M['wood'] = mat_wood()
    M['frame_paint'] = simple('Door_Frame_Paint', (0.07, 0.18, 0.20), 0.32, coat=0.3, coat_rough=0.1)
    M['steel'] = mat_brushed()
    M['chrome'] = simple('Chrome', (0.92, 0.92, 0.92), 0.06, metal=1.0)
    M['alu'] = mat_brushed('Aluminium', (0.78, 0.79, 0.80), 0.3, 0.45)
    M['metal_dark'] = simple('Metal_Painted_Grey', (0.22, 0.23, 0.24), 0.4, metal=0.5)
    M['white_plastic'] = simple('Plastic_White', (0.82, 0.83, 0.81), 0.35, bump=0.02)
    M['beige_plastic'] = simple('Plastic_Beige', (0.74, 0.70, 0.62), 0.4)
    M['grey_plastic'] = simple('Plastic_Grey', (0.35, 0.37, 0.38), 0.4)
    M['black_plastic'] = simple('Plastic_Black', (0.02, 0.02, 0.022), 0.35)
    M['rubber'] = simple('Rubber_Black', (0.015, 0.015, 0.015), 0.75)
    M['red'] = simple('Paint_Red', (0.55, 0.025, 0.03), 0.3, coat=0.4)
    M['blue'] = simple('Plastic_Blue', (0.04, 0.22, 0.52), 0.32)
    M['yellow'] = simple('Plastic_Yellow', (0.85, 0.6, 0.02), 0.35)
    M['green_tank'] = simple('Paint_Oxygen_Green', (0.03, 0.26, 0.10), 0.3, coat=0.5, coat_rough=0.1)
    M['white_paint'] = simple('Paint_White_Gloss', (0.85, 0.85, 0.84), 0.2, coat=0.4)
    M['mattress'] = simple('Vinyl_Mattress', (0.05, 0.18, 0.30), 0.4, coat=0.2)
    M['sheet'] = mat_fabric('Fabric_Sheet', (0.80, 0.83, 0.85), 0.4, 1200, 0.9)
    M['blanket'] = mat_fabric('Fabric_Blanket', (0.30, 0.46, 0.58), 0.6, 600, 0.95)
    M['curtain'] = mat_fabric('Fabric_Curtain', (0.55, 0.70, 0.72), 0.5, 500, 0.85,
                              check=(0.65, 0.78, 0.78))
    M['vinyl_seat'] = simple('Vinyl_Black', (0.03, 0.03, 0.035), 0.45, coat=0.2)
    M['vinyl_teal'] = simple('Vinyl_Teal', (0.04, 0.20, 0.22), 0.4, coat=0.2)
    M['glass'] = mat_glass()
    M['glass_frosted'] = simple('Glass_Frosted_Lit', (0.6, 0.6, 0.55), 0.4, emit=(1.0, 0.72, 0.45),
                                emit_strength=2.0)
    M['glass_dark'] = simple('Glass_Frosted_Dark', (0.05, 0.06, 0.07), 0.15)
    M['iv_bag'] = mat_glass('IV_Bag', (0.9, 0.95, 1.0), 0.35)
    M['light_on'] = mat_light_panel()
    M['light_off'] = simple('Light_Panel_Off', (0.62, 0.63, 0.64), 0.3)
    M['light_warm'] = mat_emit('Emit_Warm', (1.0, 0.72, 0.45), 6.0)
    M['light_flicker'] = mat_light_panel('Light_Panel_Flicker', (0.88, 0.94, 1.0), 9.0)
    M['exit_green'] = mat_emit('Emit_Exit_Green', (0.15, 1.0, 0.35), 5.0)
    M['sign_panel'] = simple('Sign_Panel_Navy', (0.02, 0.08, 0.16), 0.3, coat=0.3)
    M['sign_text'] = mat_emit('Sign_Text_White', (0.95, 0.97, 1.0), 0.8)
    M['sign_text_dark'] = simple('Sign_Text_Dark', (0.02, 0.03, 0.04), 0.4)
    M['sky'] = mat_sky()
    M['city'] = mat_city()
    M['city_far'] = mat_city('City_Far', (0.9, 0.75, 0.6), 0.22, 2.0)
    M['screen_ecg'] = mat_screen('Screen_ECG', strength=2.5)
    M['screen_ui'] = mat_screen('Screen_UI', (0.03, 0.06, 0.12), (0.25, 0.5, 0.9), 1.6, 'ui')
    M['cork'] = mat_cork()
    M['paper_white'] = simple('Paper_White', (0.85, 0.85, 0.82), 0.85)
    M['paper_yellow'] = simple('Paper_Yellow', (0.9, 0.8, 0.35), 0.85)
    M['paper_pink'] = simple('Paper_Pink', (0.85, 0.5, 0.55), 0.85)
    M['paper_blue'] = simple('Paper_Blue', (0.45, 0.65, 0.85), 0.85)
    M['paper_green'] = simple('Paper_Green', (0.55, 0.8, 0.5), 0.85)
    M['whiteboard'] = simple('Whiteboard', (0.88, 0.89, 0.9), 0.12, coat=0.6)
    M['marker'] = simple('Marker_Ink', (0.05, 0.12, 0.45), 0.5)
    M['counter_top'] = simple('Solid_Surface', (0.86, 0.85, 0.82), 0.25, coat=0.3, bump=0.02)
    M['binder_r'] = simple('Binder_Red', (0.45, 0.05, 0.04), 0.5)
    M['binder_b'] = simple('Binder_Blue', (0.04, 0.12, 0.35), 0.5)
    M['binder_g'] = simple('Binder_Green', (0.08, 0.30, 0.12), 0.5)
    M['binder_k'] = simple('Binder_Black', (0.03, 0.03, 0.03), 0.5)
    M['leaf'] = simple('Plant_Leaf', (0.05, 0.20, 0.05), 0.45, sheen=0.3)
    M['soil'] = simple('Soil', (0.05, 0.035, 0.02), 0.95)
    M['pot'] = simple('Ceramic_Pot', (0.75, 0.73, 0.70), 0.25, coat=0.5)
    M['gauge_face'] = simple('Gauge_Face', (0.9, 0.9, 0.88), 0.2)
    M['clock_face'] = simple('Clock_Face', (0.92, 0.92, 0.9), 0.3)
    M['gas_green'] = simple('Gas_Outlet_Green', (0.05, 0.45, 0.15), 0.3)
    M['gas_white'] = simple('Gas_Outlet_White', (0.9, 0.9, 0.9), 0.3)
    M['gas_yellow'] = simple('Gas_Outlet_Yellow', (0.85, 0.7, 0.05), 0.3)
    M['dark_void'] = simple('Void_Black', (0.0, 0.0, 0.0), 1.0, spec=0.0)
    M['ground'] = simple('Ground_Dusk', (0.02, 0.02, 0.025), 0.9)
    return M


def M(key):
    return _CACHE[key]


def rods(name, segs, r, mat, col, seg=10, loc=(0, 0, 0), rot=(0, 0, 0), parent=None):
    """Many straight cylinders merged into one mesh (frames, spokes, legs)."""
    bm = bmesh.new()
    for spec in segs:
        a, b = Vector(spec[0]), Vector(spec[1])
        rr = spec[2] if len(spec) > 2 else r
        d = b - a
        if d.length < 1e-6:
            continue
        q = d.to_track_quat('Z', 'Y')
        mtx = Matrix.Translation((a + b) / 2) @ q.to_matrix().to_4x4()
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg, radius1=rr,
                              radius2=rr, depth=d.length, matrix=mtx)
    return _finish(bm, name, col, mat, loc, rot, True, 40 * D2R, parent)


def poly_prism(name, pts2d, depth, mat, col, loc=(0, 0, 0), rot=(0, 0, 0), parent=None):
    """Extrude a 2D outline (XY) along Z by depth (arrows, sign glyphs)."""
    bm = bmesh.new()
    bot = [bm.verts.new((x, y, 0)) for x, y in pts2d]
    top = [bm.verts.new((x, y, depth)) for x, y in pts2d]
    bm.faces.new(list(reversed(bot)))
    bm.faces.new(top)
    n = len(pts2d)
    for i in range(n):
        bm.faces.new((bot[i], bot[(i + 1) % n], top[(i + 1) % n], top[i]))
    return _finish(bm, name, col, mat, loc, rot, False, None, parent)
