"""Step 4: ruins of the old dwarven hall: octagonal columns built from offset drums (intact, broken, stump),
a fallen column, scattered carved blocks, and stairs up to a gate carved into the cave wall."""
import bpy, bmesh, os, sys, random, math, importlib
from mathutils import Vector, Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import layout as L, dc
importlib.reload(L); importlib.reload(dc)

rng = random.Random(L.SEED + 4)
M = dc.materials()
col = dc.coll('04_Ruins')
dc.clear(col)
bm = bmesh.new()
dark = dc.mat_simple('DC_GateDark', (0.0, 0.0, 0.0), rough=1.0)


def prism(center, r_bot, r_top, h, sides=8, rot=None, jag=0.0, twist=0.0):
    """Faceted prism from center (bottom) upwards along rot's Z axis; jag lowers top vertices randomly."""
    rot = rot or Matrix.Identity(3)
    off = rng.random() * 0.5 if twist else math.pi / sides
    bot = [bm.verts.new(center + rot @ Vector((math.cos(off + i * 2 * math.pi / sides) * r_bot,
                                                math.sin(off + i * 2 * math.pi / sides) * r_bot, 0))) for i in range(sides)]
    top = [bm.verts.new(center + rot @ Vector((math.cos(off + twist + i * 2 * math.pi / sides) * r_top,
                                                math.sin(off + twist + i * 2 * math.pi / sides) * r_top,
                                                h - (rng.random() * jag if jag else 0)))) for i in range(sides)]
    for i in range(sides):
        bm.faces.new((bot[i], bot[(i + 1) % sides], top[(i + 1) % sides], top[i]))
    bm.faces.new(list(reversed(bot)))
    if jag:                                    # broken top: a fan to a low centre point
        c = bm.verts.new(center + rot @ Vector((0, 0, h - jag * (0.3 + rng.random() * 0.5))))
        for i in range(sides):
            bm.faces.new((top[i], top[(i + 1) % sides], c))
    else:
        bm.faces.new(top)


def box(center, size, rz=0.0, tilt=(0.0, 0.0)):
    rot = Matrix.Rotation(rz, 3, 'Z') @ Matrix.Rotation(tilt[0], 3, 'X') @ Matrix.Rotation(tilt[1], 3, 'Y')
    sx, sy, sz = (s / 2 for s in size)
    vs = [bm.verts.new(center + rot @ dc.jitter(Vector((x * sx, y * sy, z * sz)), rng, min(size) * 0.08))
          for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
    for f in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)):
        bm.faces.new([vs[i] for i in f])


def column(x, y, height, state):
    r = L.COLUMN_R
    p = Vector((x, y, L.FLOOR_Z - 0.1))
    box(p + Vector((0, 0, 0.35)), (r * 3.0, r * 3.0, 0.7), rz=rng.random() * 0.1)       # square plinth
    prism(p + Vector((0, 0, 0.7)), r * 1.35, r * 1.2, 0.55)                               # base moulding
    z, top = 1.25, (height or L.COLUMN_H) - (1.2 if state == 'intact' else 0)
    while z < top - 0.05:
        dh = min(1.7, top - z)
        last = z + dh >= top - 0.05
        jag = 0.6 if last and state != 'intact' else 0.0
        drum = Matrix.Rotation((rng.random() - .5) * 0.035, 3, 'X') @ Matrix.Rotation((rng.random() - .5) * 0.035, 3, 'Y')
        prism(p + Vector(((rng.random() - .5) * 0.06, (rng.random() - .5) * 0.06, z)), r, r * 0.97, dh - 0.03,
              rot=drum, jag=jag, twist=(rng.random() - .5) * 0.12)
        z += dh
    if state == 'intact':                                                                 # capital and abacus
        prism(p + Vector((0, 0, z)), r * 0.97, r * 1.45, 0.7)
        box(p + Vector((0, 0, z + 0.95)), (r * 3.3, r * 3.3, 0.5), rz=rng.random() * 0.1)
    for _ in range(4 if state != 'intact' else 2):                                        # fallen fragments
        a = rng.random() * 6.28
        d = r * (2.0 + rng.random() * 2.5)
        s = 0.4 + rng.random() * 0.7
        box(Vector((x + math.cos(a) * d, y + math.sin(a) * d, L.FLOOR_Z + s * 0.3)), (s * 1.3, s, s * 0.8),
            rz=rng.random() * 3, tilt=((rng.random() - .5) * 0.5, (rng.random() - .5) * 0.5))


for x, y, h, state in L.COLUMNS:
    column(x, y, h, state)

# fallen column: drums lying along a line, slightly scattered
fc = L.FALLEN_COLUMN
d = Vector((math.cos(math.radians(fc['angle'])), math.sin(math.radians(fc['angle'])), 0))
lie = Vector((0, 0, 1)).rotation_difference(d).to_matrix()
pos = Vector((fc['start'][0], fc['start'][1], L.FLOOR_Z + L.COLUMN_R * 0.85))
for k in range(fc['drums']):
    j = Matrix.Rotation((rng.random() - .5) * 0.25, 3, 'Z')
    prism(pos + Vector(((rng.random() - .5) * 0.3, (rng.random() - .5) * 0.3, 0)), L.COLUMN_R, L.COLUMN_R * 0.97, 1.55,
          rot=j @ lie, twist=(rng.random() - .5) * 0.3)
    pos += d * (1.7 + rng.random() * 0.35)

# stairs climbing to a gate carved into the wall
st = L.STAIRS
rot = Matrix.Rotation(math.radians(st['rot']), 3, 'Z')
base = Vector((st['x'], st['y'], L.FLOOR_Z))
fwd = rot @ Vector((0, -1, 0))                 # climbing direction (rot -90 -> towards -X, the wall)
for i in range(st['steps']):
    h = 0.38 * (i + 1)
    for k, w in enumerate((st['width'] * 0.36, st['width'] * 0.36)):   # two worn half-blocks per step
        lat = rot @ Vector(((k - 0.5) * st['width'] * 0.5 + (rng.random() - .5) * 0.1, 0, 0))
        box(base + fwd * (0.65 * i) + lat + Vector((0, 0, h / 2 - 0.05)), (w * 1.35, 0.68, h), rz=math.radians(st['rot']))
top = base + fwd * (0.65 * st['steps'] + 1.2)
box(top + Vector((0, 0, 0.38 * st['steps'] / 2 - 0.05)), (st['width'] * 1.05, 2.4, 0.38 * st['steps']), rz=math.radians(st['rot']))
gate = top + fwd * 1.5 + Vector((0, 0, 0.38 * st['steps']))
lat = rot @ Vector((1, 0, 0))
for s in (-1, 1):                              # gate posts and lintel
    box(gate + lat * s * 2.4 + Vector((0, 0, 3.0)), (1.4, 1.6, 6.0), rz=math.radians(st['rot']))
box(gate + Vector((0, 0, 6.6)), (6.6, 1.8, 1.3), rz=math.radians(st['rot']))
prism(gate + Vector((0, 0, 7.25)), 1.4, 0.2, 1.2, sides=4, rot=Matrix.Rotation(math.radians(st['rot']), 3, 'Z'))

ruins = dc.bm_to_obj(bm, 'Ruins', col, [M['stone']], var=0.55, rng=rng)
# darkness inside the gate
bm = bmesh.new()
g0 = gate + fwd * 0.6
vs = [bm.verts.new(g0 + lat * a + Vector((0, 0, z))) for a, z in ((-1.75, 0), (1.75, 0), (1.75, 6.0), (-1.75, 6.0))]
bm.faces.new(vs)
dc.bm_to_obj(bm, 'Gate_Dark', col, [dark], var=0.0)
print('ruins ok:', len(ruins.data.polygons), 'faces')
