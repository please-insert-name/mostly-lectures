"""Step 1: cave shell with floor and ceiling hole, stalactites, stalagmites, boulders, sky above the hole."""
import bpy, bmesh, os, sys, random, math, importlib
from mathutils import Vector, noise, Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import layout as L, dc
importlib.reload(L); importlib.reload(dc)

rng = random.Random(L.SEED)
M = dc.materials()
col = dc.coll('01_Cave')
dc.clear(col)
C = Vector(L.CAVE_CENTER)
HX, HY = L.HOLE_XY


def hole_radius(p):
    a = math.atan2(p.y - HY, p.x - HX)
    return L.HOLE_R * (1.0 + 0.22 * math.sin(3 * a + 1.3) + 0.12 * math.sin(7 * a))


def dist_hole(p):
    return math.hypot(p.x - HX, p.y - HY)


def dist_hoard(x, y):
    return math.hypot(x - L.HOARD_XY[0], y - L.HOARD_XY[1])


# ---------------------------------------------------------------- shell
bm = bmesh.new()
bmesh.ops.create_icosphere(bm, subdivisions=5, radius=1.0)
n = L.CAVE_NOISE
for v in bm.verts:
    d = v.co.copy()
    p = C + Vector((d.x * L.CAVE_RADII[0], d.y * L.CAVE_RADII[1], d.z * L.CAVE_RADII[2]))
    off = noise.noise(p * n['freq']) * n['amp'] + noise.noise(p * n['freq2'] + Vector((5, 5, 5))) * n['amp2']
    p += d.normalized() * off
    if p.z < L.FLOOR_Z + 0.6:                                   # flatten the bowl into a floor
        p.z = L.FLOOR_Z + noise.noise(p * 0.25) * 0.35
    v.co = p
# the ceiling hole: delete the faces inside an irregular outline
dead = [f for f in bm.faces if f.calc_center_median().z > 12 and dist_hole(f.calc_center_median()) < hole_radius(f.calc_center_median())]
bmesh.ops.delete(bm, geom=dead, context='FACES')
bmesh.ops.reverse_faces(bm, faces=bm.faces[:])              # normals point into the cave
bm.normal_update()
floor_faces, moss_faces = 0, 0
for f in bm.faces:
    c = f.calc_center_median()
    if c.z < L.FLOOR_Z + 0.8:
        f.material_index = 2                                     # floor
        floor_faces += 1
    elif dist_hole(c) < L.HOLE_R + 5.5 and c.z > 12:
        f.material_index = 1                                     # moss creeps over the rim of the hole
        moss_faces += 1
shell = dc.bm_to_obj(bm, 'Cave_Shell', col, [M['rock'], M['rock_moss'], M['floor']], var=0.6, rng=rng)
sol = shell.modifiers.new('Thickness', 'SOLIDIFY')
sol.thickness, sol.offset, sol.use_even_offset = 2.0, -1.0, False

# moss patch on the floor below the hole
pp = L.PLANT_PATCH
for f in shell.data.polygons:
    c = f.center
    if f.material_index == 2 and math.hypot(c.x - pp['center'][0], c.y - pp['center'][1]) < pp['radius'] * (0.7 + 0.5 * rng.random()):
        f.material_index = 1

# ---------------------------------------------------------------- stalactites / stalagmites
def spike(bm, base, direction, r, length, sides=None):
    """Faceted two-segment cone from base along direction (tip at base + direction * length)."""
    sides = sides or rng.choice((5, 6, 7))
    d = direction.normalized()
    q = d.to_track_quat('Z', 'Y')
    rings = []
    for t, rr in ((-0.6, r * 1.05), (0.0, r), (0.45, r * (0.45 + 0.2 * rng.random()))):
        ring = []
        for i in range(sides):
            a = 2 * math.pi * i / sides + rng.random() * 0.4
            local = Vector((math.cos(a) * rr, math.sin(a) * rr, t * length))
            ring.append(bm.verts.new(base + q @ dc.jitter(local, rng, rr * 0.25)))
        rings.append(ring)
    tip = bm.verts.new(base + d * length + Vector(((rng.random() - .5) * r * .4, (rng.random() - .5) * r * .4, 0)))
    for a, b in zip(rings, rings[1:]):
        for i in range(sides):
            bm.faces.new((a[i], a[(i + 1) % sides], b[(i + 1) % sides], b[i]))
    for i in range(sides):
        bm.faces.new((rings[-1][i], rings[-1][(i + 1) % sides], tip))
    bm.faces.new(list(reversed(rings[0])))


ceiling = [p for p in shell.data.polygons
           if p.center.z > 13 and p.normal.z < -0.55 and dist_hole(p.center) > L.HOLE_R + 3.0]
bm = bmesh.new()
for p in rng.sample(ceiling, min(70, len(ceiling))):
    r = 0.35 + rng.random() ** 2 * 1.1
    spike(bm, p.center.copy() + Vector((0, 0, 0.4)), Vector(((rng.random() - .5) * .25, (rng.random() - .5) * .25, -1)),
          r, r * (3.5 + rng.random() * 4.0))
stal = 0
while stal < 46:
    a, rad = rng.random() * 2 * math.pi, 9 + rng.random() * 12
    x, y = C.x + math.cos(a) * rad, C.y + math.sin(a) * rad
    if dist_hoard(x, y) < L.HOARD_R + 1.5 or math.hypot(x - L.STAIRS['x'], y - L.STAIRS['y']) < 6 \
            or math.hypot(x - pp['center'][0], y - pp['center'][1]) < pp['radius'] \
            or (y < -3 and abs(x) < 15):                       # keep the wide shot's foreground open
        continue
    r = 0.25 + rng.random() ** 2 * 0.65
    spike(bm, Vector((x, y, L.FLOOR_Z - 0.2)), Vector(((rng.random() - .5) * .2, (rng.random() - .5) * .2, 1)),
          r, r * (2.5 + rng.random() * 3.5))
    stal += 1
dc.bm_to_obj(bm, 'Cave_Spikes', col, [M['rock']], var=0.6, rng=rng)

# ---------------------------------------------------------------- boulders
bm = bmesh.new()
placed = 0
while placed < 38:
    a, rad = rng.random() * 2 * math.pi, 6 + rng.random() ** 0.6 * 16
    x, y = C.x + math.cos(a) * rad, C.y + math.sin(a) * rad
    if dist_hoard(x, y) < L.HOARD_R + 0.5 or math.hypot(x - L.STAIRS['x'], y - L.STAIRS['y']) < 5 \
            or (y < -3 and abs(x) < 12):                       # keep the wide shot's foreground open
        continue
    s = 0.4 + rng.random() ** 2 * 2.2
    tmp = bmesh.new()
    bmesh.ops.create_icosphere(tmp, subdivisions=1, radius=1.0)
    rot = Matrix.Rotation(rng.random() * 6.3, 3, 'Z')
    sq = Vector((s * (0.8 + rng.random() * .6), s * (0.8 + rng.random() * .6), s * (0.45 + rng.random() * .35)))
    verts = [rot @ Vector((v.co.x * sq.x, v.co.y * sq.y, v.co.z * sq.z)) for v in tmp.verts]
    nv = [bm.verts.new(dc.jitter(p, rng, s * 0.35) + Vector((x, y, L.FLOOR_Z + sq.z * 0.35))) for p in verts]
    for f in tmp.faces:
        bm.faces.new([nv[v.index] for v in f.verts])
    tmp.free()
    placed += 1
dc.bm_to_obj(bm, 'Cave_Boulders', col, [M['rock']], var=0.6, rng=rng)

# ---------------------------------------------------------------- sky seen through the hole (casts no shadow)
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=30)
sky = dc.bm_to_obj(bm, 'Sky_Plane', col, [M['sky']], var=0.0, loc=(HX, HY, 42))
sky.visible_shadow = False
sky.rotation_euler = (math.pi, 0, 0)

print('cave ok: shell', len(shell.data.polygons), 'faces,', floor_faces, 'floor,', moss_faces, 'moss rim')
