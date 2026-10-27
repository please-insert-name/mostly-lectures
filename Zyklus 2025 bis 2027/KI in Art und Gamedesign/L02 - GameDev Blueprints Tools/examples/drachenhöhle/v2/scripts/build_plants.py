"""Step 6: plants where light reaches: ferns and moss cushions under the hole, vines hanging from its rim."""
import bpy, bmesh, os, sys, random, math, importlib
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import layout as L, dc
importlib.reload(L); importlib.reload(dc)

rng = random.Random(L.SEED + 6)
M = dc.materials()
col = dc.coll('06_Plants')
dc.clear(col)
dg = bpy.context.evaluated_depsgraph_get()
shell = BVHTree.FromObject(bpy.data.objects['Cave_Shell'], dg)
pp = L.PLANT_PATCH
HX, HY = L.HOLE_XY


def floor_at(x, y):
    hit = shell.ray_cast(Vector((x, y, 6)), Vector((0, 0, -1)))
    return hit[0] if hit[0] else Vector((x, y, L.FLOOR_Z))


# ferns (imported template, instanced)
fern_src = bpy.data.collections['A_Fern']
for k in range(30):
    a, r = rng.random() * 6.28, pp['radius'] * math.sqrt(rng.random()) * 1.1
    p = floor_at(pp['center'][0] + math.cos(a) * r, pp['center'][1] + math.sin(a) * r)
    o = bpy.data.objects.new(f'Fern_{k:02d}', None)
    o.instance_type, o.instance_collection = 'COLLECTION', fern_src
    o.location = p
    o.rotation_euler = ((rng.random() - .5) * 0.2, (rng.random() - .5) * 0.2, rng.random() * 6.28)
    o.scale = (0.7 + rng.random() * 1.2,) * 3
    col.objects.link(o)

# moss cushions: flattened faceted blobs
bm = bmesh.new()
for _ in range(16):
    a, r = rng.random() * 6.28, pp['radius'] * math.sqrt(rng.random())
    c = floor_at(pp['center'][0] + math.cos(a) * r, pp['center'][1] + math.sin(a) * r)
    s = 0.5 + rng.random() * 1.1
    tmp = bmesh.new()
    bmesh.ops.create_icosphere(tmp, subdivisions=2, radius=1.0)
    nv = [bm.verts.new(dc.jitter(Vector((v.co.x * s * 1.3, v.co.y * s, max(v.co.z, -0.2) * s * 0.35)), rng, s * 0.12) + c)
          for v in tmp.verts]
    for f in tmp.faces:
        bm.faces.new([nv[v.index] for v in f.verts])
    tmp.free()
dc.bm_to_obj(bm, 'Moss_Cushions', col, [M['moss']], var=0.7, rng=rng)

# vines from the rim of the hole: thin three-sided strands with alternating leaf triangles
bm = bmesh.new()
n = 0
for k in range(34):
    a = k / 34 * 6.283 + rng.random() * 0.15
    rr = L.HOLE_R * (1.1 + rng.random() * 0.5)
    x, y = HX + math.cos(a) * rr, HY + math.sin(a) * rr
    hit = shell.ray_cast(Vector((x, y, 12)), Vector((0, 0, 1)))
    if not hit[0] or rng.random() < 0.25:
        continue
    top = hit[0] + Vector((0, 0, 0.3))
    length = 2.5 + rng.random() ** 1.5 * 9.0
    segs = max(4, int(length / 0.6))
    sway = Vector((rng.random() - .5, rng.random() - .5, 0)) * 0.5
    prev = None
    for i in range(segs + 1):
        t = i / segs
        c = top + Vector((0, 0, -length * t)) + sway * math.sin(t * 3.0) * t
        w = 0.035 * (1 - 0.6 * t)
        ring = [bm.verts.new(c + Vector((math.cos(j * 2.094) * w, math.sin(j * 2.094) * w, 0))) for j in range(3)]
        if prev:
            for j in range(3):
                bm.faces.new((prev[j], prev[(j + 1) % 3], ring[(j + 1) % 3], ring[j]))
        prev = ring
        if 0 < i < segs and rng.random() < 0.8:                       # leaf
            d = Matrix.Rotation(rng.random() * 6.28, 3, 'Z') @ Vector((1, 0, 0))
            ls = 0.12 + rng.random() * 0.12
            p0 = c
            p1 = c + d * ls * 0.5 + Vector((0, 0, ls * 0.35)) + d.cross(Vector((0, 0, 1))) * ls * 0.35
            p2 = c + d * ls * 1.2 + Vector((0, 0, -ls * 0.2))
            p3 = c + d * ls * 0.5 + Vector((0, 0, ls * 0.35)) - d.cross(Vector((0, 0, 1))) * ls * 0.35
            lv = [bm.verts.new(p) for p in (p0, p1, p2, p3)]
            f = bm.faces.new(lv)
            f.material_index = 1
    n += 1
dc.bm_to_obj(bm, 'Vines', col, [M['moss'], M['leaf']], var=0.6, rng=rng)
print('plants ok:', n, 'vines')
