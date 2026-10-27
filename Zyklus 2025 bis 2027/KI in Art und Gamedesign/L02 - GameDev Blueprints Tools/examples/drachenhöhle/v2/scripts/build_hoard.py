"""Step 2: the treasure mound. A faceted gold hill, coins and gems scattered on it with Geometry Nodes, coins
spilling onto the floor, and the imported treasures (crowns, chalices, ingots, chests, bones) set into the surface."""
import bpy, bmesh, os, sys, random, math, importlib
from mathutils import Vector, noise, Matrix
from mathutils.bvhtree import BVHTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import layout as L, dc
importlib.reload(L); importlib.reload(dc)

rng = random.Random(L.SEED + 1)
M = dc.materials()
col = dc.coll('02_Hoard')
dc.clear(col)
tpl = dc.coll('_Templates')
HX, HY = L.HOARD_XY
R, H = L.HOARD_R, L.HOARD_H

# sub-mounds make the silhouette lumpy instead of a perfect dome
BUMPS = [(HX + math.cos(a) * d, HY + math.sin(a) * d, s, h) for a, d, s, h in
         [(rng.random() * 6.28, R * (0.35 + rng.random() * 0.45), 1.6 + rng.random() * 2.2, 0.4 + rng.random() * 0.9)
          for _ in range(9)]] + [L.HEAD_PILE]


def height(x, y):
    r = math.hypot(x - HX, y - HY) / R
    h = H * max(0.0, 1.0 - r * r) ** 1.15 - 0.35 * r
    for bx, by, s, bh in BUMPS:
        h += bh * math.exp(-((x - bx) ** 2 + (y - by) ** 2) / (s * s))
    return h + noise.noise(Vector((x, y, 0)) * 0.45) * 0.22


# ---------------------------------------------------------------- mound mesh
bm = bmesh.new()
step = 0.75
n = int(R * 1.25 / step)
grid = {}
for i in range(-n, n + 1):
    for j in range(-n, n + 1):
        x = HX + i * step + (j % 2) * step * 0.5 + (rng.random() - .5) * step * 0.45
        y = HY + j * step * 0.866 + (rng.random() - .5) * step * 0.45
        if math.hypot(x - HX, y - HY) <= R * 1.12:
            grid[i, j] = bm.verts.new((x, y, max(height(x, y), -0.5)))
for (i, j), v in grid.items():
    o = j % 2                                            # offset rows -> triangle fan pattern
    for a, b in (((i + o, j + 1), (i + 1, j)), ((i + o - 1, j + 1), (i + o, j + 1))):
        if a in grid and b in grid:
            try:
                bm.faces.new((v, grid[b], grid[a]))
            except ValueError:
                pass
bm.normal_update()
for f in bm.faces:
    if f.normal.z < 0:
        f.normal_flip()
mound = dc.bm_to_obj(bm, 'Hoard_Mound', col, [M['gold_mound']], var=0.7, rng=rng)


# ---------------------------------------------------------------- templates: coin and gems
def template(name, bm, mats):
    o = bpy.data.objects.get(name)
    if o:
        bpy.data.objects.remove(o)
    return dc.bm_to_obj(bm, name, tpl, mats, var=0.8, rng=rng)


bm = bmesh.new()
ret = bmesh.ops.create_circle(bm, cap_ends=True, segments=8, radius=0.08)
ex = bmesh.ops.extrude_face_region(bm, geom=bm.faces[:])
bmesh.ops.translate(bm, vec=(0, 0, 0.018), verts=[e for e in ex['geom'] if isinstance(e, bmesh.types.BMVert)])
coin = template('T_Coin', bm, [M['gold']])
coin_col = dc.coll('T_Coins', tpl)            # Object Info can't read objects in excluded collections; Collection Info can
for c in list(coin.users_collection):
    c.objects.unlink(coin)
coin_col.objects.link(coin)

gems = []
for k, (gname, gm) in enumerate((('T_GemRed', 'gem_red'), ('T_GemGreen', 'gem_green'), ('T_GemBlue', 'gem_blue'))):
    bm = bmesh.new()
    top, bot = bm.verts.new((0, 0, 0.12)), bm.verts.new((0, 0, -0.07))
    ring = [bm.verts.new((math.cos(a) * 0.09, math.sin(a) * 0.09, 0.02)) for a in [i * math.pi / 3 for i in range(6)]]
    for i in range(6):
        bm.faces.new((ring[i], ring[(i + 1) % 6], top))
        bm.faces.new((ring[(i + 1) % 6], ring[i], bot))
    gems.append(template(gname, bm, [M[gm]]))
gem_col = dc.coll('T_Gems', tpl)
for g in gems:
    for c in list(g.users_collection):
        c.objects.unlink(g)
    gem_col.objects.link(g)
    g.location = (0, 0, 0)


# hero crown: faceted band, six pointed tips, gems set into the band (reads clearly as a crown in close-up)
def hero_crown_template():
    bm = bmesh.new()
    seg, ro, ri, h = 16, 0.24, 0.21, 0.16           # a tall band, so the ring reads above the coins
    ring = lambda r, z: [bm.verts.new((math.cos(2 * math.pi * i / seg) * r, math.sin(2 * math.pi * i / seg) * r, z))
                         for i in range(seg)]
    ob, ib, ot, it = ring(ro, 0), ring(ri, 0), ring(ro, h), ring(ri, h)
    for i in range(seg):
        j = (i + 1) % seg
        bm.faces.new((ob[i], ob[j], ot[j], ot[i]))
        bm.faces.new((ib[j], ib[i], it[i], it[j]))
        bm.faces.new((ot[i], ot[j], it[j], it[i]))
        bm.faces.new((ib[i], ib[j], ob[j], ob[i]))
    for k in range(8):                                  # tips rise from every second band segment
        i, j = 2 * k, 2 * k + 1
        a = 2 * math.pi * (i + 0.5) / seg
        tip = bm.verts.new((math.cos(a) * (ro + ri) / 2 * 1.04, math.sin(a) * (ro + ri) / 2 * 1.04, h + 0.13))
        bm.faces.new((ot[i], ot[j], tip))
        bm.faces.new((it[j], it[i], tip))
        bm.faces.new((it[i], ot[i], tip))
        bm.faces.new((ot[j], it[j], tip))
    for k in range(8):                                  # gems on the band between the tips
        a = 2 * math.pi * (2 * k + 1.5) / seg
        c = Vector((math.cos(a) * (ro + 0.012), math.sin(a) * (ro + 0.012), h * 0.5))
        out = Vector((math.cos(a), math.sin(a), 0))
        side = Vector((-math.sin(a), math.cos(a), 0))
        g = 0.03
        vs = [bm.verts.new(c + d) for d in (out * g, side * g, -side * g, Vector((0, 0, g)), Vector((0, 0, -g)), -out * g * 0.3)]
        for f in ((0, 1, 3), (0, 3, 2), (0, 2, 4), (0, 4, 1), (5, 3, 1), (5, 2, 3), (5, 4, 2), (5, 1, 4)):
            face = bm.faces.new([vs[x] for x in f])
            face.material_index = 1 + k % 3
    polished = dc.mat_gold('DC_GoldPolished', rough=0.26)   # brighter, smoother than the coins (a mirror would only show the dark cave)
    o = template('T_HeroCrown', bm, [polished, M['gem_red'], M['gem_green'], M['gem_blue']])
    c = dc.coll('T_HeroCrown', tpl)
    for uc in list(o.users_collection):
        uc.objects.unlink(o)
    c.objects.link(o)
    return c


hero_crown_col = hero_crown_template()

# ---------------------------------------------------------------- scatter with geometry nodes
def scatter(obj, name, inst, density, scale=(0.8, 1.25), tilt=0.5, pick=False, seed=0, keep_base=True):
    ng = bpy.data.node_groups.get(name)
    if ng:
        bpy.data.node_groups.remove(ng)
    ng = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    N, Lk = ng.nodes, ng.links
    gi, go = N.new('NodeGroupInput'), N.new('NodeGroupOutput')
    dist = N.new('GeometryNodeDistributePointsOnFaces')
    dist.inputs['Density'].default_value = density
    dist.inputs['Seed'].default_value = seed
    Lk.new(gi.outputs[0], dist.inputs['Mesh'])
    src = N.new('GeometryNodeCollectionInfo' if pick else 'GeometryNodeObjectInfo')
    if pick:
        src.inputs['Collection'].default_value = inst
        src.inputs['Separate Children'].default_value = True
        src.inputs['Reset Children'].default_value = True
    else:
        src.inputs['Object'].default_value = inst
    align = N.new('FunctionNodeAlignRotationToVector')
    Lk.new(dist.outputs['Normal'], align.inputs['Vector'])
    iop = N.new('GeometryNodeInstanceOnPoints')
    Lk.new(dist.outputs['Points'], iop.inputs['Points'])
    Lk.new(src.outputs[0], iop.inputs['Instance'])
    Lk.new(align.outputs[0], iop.inputs['Rotation'])
    if pick:
        iop.inputs['Pick Instance'].default_value = True
        ri = N.new('FunctionNodeRandomValue')
        ri.data_type = 'INT'
        ri.inputs['Min'].default_value, ri.inputs['Max'].default_value = 0, 99
        ri.inputs['Seed'].default_value = seed + 3
        Lk.new(ri.outputs['Value'], iop.inputs['Instance Index'])
    rs = N.new('FunctionNodeRandomValue')
    rs.data_type = 'FLOAT'
    rs.inputs['Min'].default_value, rs.inputs['Max'].default_value = scale
    rs.inputs['Seed'].default_value = seed + 1
    Lk.new(rs.outputs['Value'], iop.inputs['Scale'])
    rr = N.new('FunctionNodeRandomValue')
    rr.data_type = 'FLOAT_VECTOR'
    rr.inputs['Min'].default_value = (-tilt, -tilt, 0)
    rr.inputs['Max'].default_value = (tilt, tilt, 6.283)
    rr.inputs['Seed'].default_value = seed + 2
    rot = N.new('GeometryNodeRotateInstances')
    rot.inputs['Local Space'].default_value = True
    Lk.new(iop.outputs[0], rot.inputs['Instances'])
    Lk.new(rr.outputs['Value'], rot.inputs['Rotation'])
    out = rot.outputs[0]
    if keep_base:
        j = N.new('GeometryNodeJoinGeometry')
        Lk.new(gi.outputs[0], j.inputs[0])
        Lk.new(out, j.inputs[0])
        out = j.outputs[0]
    Lk.new(out, go.inputs[0])
    mod = obj.modifiers.new(name, 'NODES')
    mod.node_group = ng
    return mod


coins = mound.copy()
coins.data = mound.data
coins.name = 'Hoard_Coins'
col.objects.link(coins)
scatter(coins, 'GN_Coins', coin_col, density=55, tilt=0.55, pick=True, seed=11, keep_base=False)
gem_obj = mound.copy()
gem_obj.name = 'Hoard_Gems'
col.objects.link(gem_obj)
scatter(gem_obj, 'GN_Gems', gem_col, density=0.05, scale=(1.2, 1.7), tilt=0.9, pick=True, seed=21, keep_base=False)

# coins spilled on the floor around the mound: a ring that only carries instances
bm = bmesh.new()
segs = 48
inner = [bm.verts.new((HX + math.cos(a) * R * 0.9, HY + math.sin(a) * R * 0.9, 0.02)) for a in [i * 6.283 / segs for i in range(segs)]]
outer = [bm.verts.new((HX + math.cos(a) * R * (1.18 + 0.12 * math.sin(5 * a)), HY + math.sin(a) * R * (1.18 + 0.12 * math.sin(5 * a)), 0.02))
         for a in [i * 6.283 / segs for i in range(segs)]]
for i in range(segs):
    bm.faces.new((inner[i], inner[(i + 1) % segs], outer[(i + 1) % segs], outer[i]))
spill = dc.bm_to_obj(bm, 'Hoard_Spill', col, [M['gold']], var=0.0)
scatter(spill, 'GN_Spill', coin_col, density=16, tilt=0.15, pick=True, seed=31, keep_base=False)

# imported treasures share the scene's gold (their own 'Gold' is olive and only 40 % metallic)
for cn in ('A_Crown', 'A_Chalice', 'A_Ingots'):
    for o in bpy.data.collections[cn].all_objects:
        for slot in getattr(o, 'material_slots', []):
            if slot.material and slot.material.name.startswith('Gold'):
                slot.material = M['gold']
# the imported skeleton is flat grey (reads as a robot): bone like the skulls
for o in bpy.data.collections['A_Skeleton'].all_objects:
    for slot in getattr(o, 'material_slots', []):
        slot.material = M['bone']

# ---------------------------------------------------------------- treasures set into the surface
dg = bpy.context.evaluated_depsgraph_get()
tree = BVHTree.FromObject(mound, dg)


def surface(x, y):
    hit = tree.ray_cast(Vector((x, y, 30)), Vector((0, 0, -1)))
    return (hit[0], hit[1]) if hit[0] else (Vector((x, y, 0)), Vector((0, 0, 1)))


def place(asset, x, y, sink=0.0, rz=0.0, tilt=0.0, scale=1.0, name=None):
    src = asset if isinstance(asset, bpy.types.Collection) else bpy.data.collections['A_' + asset]
    asset = src.name
    p, nrm = surface(x, y)
    o = bpy.data.objects.new(name or f'Treasure_{asset}', None)
    o.instance_type, o.instance_collection = 'COLLECTION', src
    q = Vector((0, 0, 1)).rotation_difference(nrm.lerp(Vector((0, 0, 1)), 1 - tilt))
    o.rotation_euler = (q.to_matrix() @ Matrix.Rotation(math.radians(rz), 3, 'Z')).to_euler()
    o.location = p - nrm * sink
    o.scale = (scale,) * 3
    col.objects.link(o)
    return o


# (asset, x, y, sink, rot_z, tilt, scale): relative to the mound centre; the dragon covers the top
TREASURES = [
    ('ChestGold', -7.4, -5.2, 0.25, 25, 0.6, 1.0), ('Chest', 7.0, -2.0, 0.35, -40, 0.7, 1.0),
    ('ChestGold', 4.8, 6.0, 0.3, 160, 0.6, 1.1), ('Chest', -7.5, 4.0, 0.5, 110, 0.8, 0.9),
    ('Crown', 5.2, -5.8, 0.08, -30, 0.5, 0.85),
    ('Chalice', -1.6, -7.0, 0.05, 0, 0.3, 1.0), ('Chalice', 1.6, -8.9, 0.0, 0, 0.0, 0.9),
    ('Chalice', -5.0, -5.5, 0.15, 0, 1.0, 1.1), ('Ingots', -4.2, -6.4, 0.1, 35, 0.7, 1.0),
    ('Ingots', 6.5, -4.4, 0.15, -20, 0.7, 1.1), ('Ingots', 1.0, -7.8, 0.1, 75, 0.6, 0.9),
    ('Ingots', -8.4, -0.5, 0.15, 10, 0.8, 1.0),
    ('Skull', -0.4, -8.7, 0.04, -20, 0.4, 1.0), ('Ribcage', 8.6, 1.5, 0.12, 60, 0.8, 1.0),
    ('Skull', 8.2, 2.3, 0.05, 140, 0.3, 1.0), ('Skull', -9.3, 3.0, 0.08, 70, 0.5, 0.9),
    ('Skeleton', -3.6, -8.2, 0.62, 205, 0.5, 1.25), ('Skull', -2.6, -8.6, 0.03, 30, 0.6, 1.0),
    ('Ribcage', -0.7, -8.9, 0.15, 120, 0.8, 0.9),
]
for asset, dx, dy, sink, rz, tilt, sc in TREASURES:
    place(asset, HX + dx, HY + dy, sink, rz, tilt, sc)


# the hero crown sits in direct sun: inside the beam cylinder through the hole, not shadowed by the dragon
def sun_spot(prefer, radius=5.0, tries=600):
    hole = Vector((L.HOLE_XY[0], L.HOLE_XY[1], 24.0))
    axis = (Vector(L.SUN_TARGET) - hole).normalized()
    dragon = BVHTree.FromObject(bpy.data.objects['DragonMesh'], dg) if 'DragonMesh' in bpy.data.objects else None
    best = None
    for _ in range(tries):
        x, y = prefer[0] + (rng.random() - .5) * 2 * radius, prefer[1] + (rng.random() - .5) * 2 * radius
        p, nrm = surface(x, y)
        q = p + Vector((0, 0, 0.25))
        rel = q - hole
        if (rel - axis * rel.dot(axis)).length > L.HOLE_R * 0.7:      # outside the shaft of sunlight
            continue
        if dragon and dragon.ray_cast(q, -axis)[0]:                   # in the dragon's shadow
            continue
        if dragon and (dragon.find_nearest(q)[0] - q).length < L.CROWN_CLEARANCE:   # the dragon must sit back, soft
            continue
        d = (Vector((x, y)) - Vector(prefer)).length
        if best is None or d < best[0]:
            best = (d, x, y)
    return best


spot = sun_spot(L.CROWN_PREFER)
if spot:
    _, cx, cy = spot
    cr = place(hero_crown_col, cx, cy, 0.0, 20, 0.35, 2.2, name='Hero_Crown')
    cr.rotation_euler.x += math.radians(14)              # tilted, partly sunk into the coins
    place('Chalice', cx + 1.1, cy + 0.6, 0.03, 0, 0.3, 1.2, name='Hero_Chalice')
    print('sun spot for the crown', round(cx, 2), round(cy, 2))
else:
    print('no sunlit spot found near', L.CROWN_PREFER)

# templates and imported assets render only through instances
vl = bpy.context.view_layer
for lc in vl.layer_collection.children:
    if lc.name in ('_Assets', '_Templates'):
        lc.exclude = True
print('hoard ok:', len(mound.data.polygons), 'mound faces,', len(TREASURES), 'treasures')
