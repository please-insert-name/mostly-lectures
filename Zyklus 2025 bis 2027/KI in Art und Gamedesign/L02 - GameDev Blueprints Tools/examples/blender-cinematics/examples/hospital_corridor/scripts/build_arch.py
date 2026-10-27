"""Step 1: reset the scene, build materials and the corridor architecture."""
import sys, os, importlib, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # __file__ is injected by bl_client.py / build_all_bg.py
import bpy
import lib, layout
importlib.reload(lib); importlib.reload(layout)
from lib import box, box_minmax, cyl, text, get_coll, M, D2R, PI
from layout import *

random.seed(4)

# ---------------------------------------------------------------- reset scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
for c in list(bpy.data.collections):
    bpy.data.collections.remove(c)
for block in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.lights,
              bpy.data.cameras, bpy.data.lightprobes):
    for d in list(block):
        block.remove(d)
bpy.data.orphans_purge(do_recursive=True)

lib.build_materials()

C_ARCH = get_coll('01_Architecture')
C_WALL = get_coll('Walls', C_ARCH)
C_TRIM = get_coll('Wall_Trim', C_ARCH)
C_CEIL = get_coll('Ceiling', C_ARCH)
C_WIN = get_coll('End_Window', C_ARCH)
C_OUT = get_coll('Exterior_Backdrop', C_ARCH)
C_STAT = get_coll('Nurse_Station_Shell', C_ARCH)

# ---------------------------------------------------------------- floor / ceiling / slab
box_minmax('Floor_Corridor', (-HW - T, Y0, -0.1), (HW + T, Y1 + 0.05, 0.0), M('floor'), C_ARCH)
box_minmax('Floor_Station', (HW + T, STATION[0] - 0.01, -0.1),
           (HW + STATION_DEPTH + T, STATION[1] + 0.01, 0.0), M('floor'), C_STAT)
box_minmax('Ceiling_Corridor', (-HW - 0.01, Y0, H), (HW + 0.01, Y1, H + 0.04), M('ceiling'), C_CEIL)
box_minmax('Ceiling_Station', (HW + T, STATION[0], H), (HW + STATION_DEPTH + 0.01, STATION[1], H + 0.04),
           M('ceiling'), C_STAT)
# structural slab above everything keeps any outside light from leaking in
box_minmax('Structure_Slab_Top', (-7.0, Y0 - 0.5, H + 0.04), (7.0, Y1 + 0.3, H + 0.5), M('dark_void'), C_ARCH)
box_minmax('Wall_Start', (-HW - T, Y0 - T, 0), (HW + T, Y0, H + 0.05), M('wall'), C_WALL)

# ---------------------------------------------------------------- side walls with openings
for side in ('L', 'R'):
    sx = side_sign(side)
    xa, xb = sorted((sx * HW, sx * (HW + T)))
    ops = openings(side)
    for i, (a, b) in enumerate(subtract(Y0, Y1, [(o[0], o[1]) for o in ops])):
        box_minmax(f'Wall_{side}_{i:02d}', (xa, a, 0), (xb, b, H + 0.04), M('wall'), C_WALL)
    for i, (a, b, top) in enumerate(ops):
        box_minmax(f'Wall_{side}_Lintel_{i:02d}', (xa, a, top), (xb, b, H + 0.04), M('wall'), C_WALL)

    # trim: skirting, protection panel, handrail with brackets
    face = sx * HW
    for i, (a, b) in enumerate(subtract(Y0, Y1, frame_zones(side))):
        if b - a < 0.05:
            continue
        def slab(name, depth, z0, z1, mat, bev=0.0):
            x0, x1 = sorted((face, face - sx * depth))
            return box_minmax(name, (x0, a, z0), (x1, b, z1), mat, C_TRIM, bevel=bev)
        slab(f'Skirting_{side}_{i:02d}', 0.012, 0.0, 0.11, M('skirting'), 0.003)
        slab(f'Panel_{side}_{i:02d}', 0.006, 0.11, 0.98, M('wall_lower'), 0.002)
        # rail (stands 6 cm off the wall)
        rx0, rx1 = sorted((face - sx * 0.045, face - sx * 0.105))
        box_minmax(f'Handrail_{side}_{i:02d}', (rx0, a + 0.03, 0.86), (rx1, b - 0.03, 0.99),
                   M('handrail'), C_TRIM, bevel=0.02, segs=3)
        n = max(1, int((b - a) / 1.2))
        for k in range(n + 1):
            y = a + 0.12 + (b - a - 0.24) * (k / max(1, n))
            bx0, bx1 = sorted((face, face - sx * 0.05))
            box_minmax(f'Rail_Bracket_{side}_{i:02d}_{k}', (bx0, y - 0.02, 0.89), (bx1, y + 0.02, 0.93),
                       M('steel'), C_TRIM, bevel=0.005)
        # bed-bumper rail low on the wall
        bx0, bx1 = sorted((face - sx * 0.006, face - sx * 0.03))
        box_minmax(f'Bumper_{side}_{i:02d}', (bx0, a + 0.02, 0.26), (bx1, b - 0.02, 0.36),
                   M('white_plastic'), C_TRIM, bevel=0.008)

# ---------------------------------------------------------------- nurse station recess shell
xs0, xs1 = HW + T, HW + STATION_DEPTH
box_minmax('Station_Wall_Back', (xs1, STATION[0] - T, 0), (xs1 + T, STATION[1] + T, H + 0.04), M('wall'), C_STAT)
# start behind the corridor wall so the reveal faces aren't doubled (z-fighting)
box_minmax('Station_Wall_S', (HW + T, STATION[0] - T, 0), (xs1, STATION[0], H + 0.04), M('wall'), C_STAT)
box_minmax('Station_Wall_N', (HW + T, STATION[1], 0), (xs1, STATION[1] + T, H + 0.04), M('wall'), C_STAT)
box_minmax('Station_Skirting', (xs1 - 0.012, STATION[0], 0), (xs1, STATION[1], 0.11), M('skirting'), C_STAT)
# stainless corner guards at the recess edges
for y, sgn in ((STATION[0], 1), (STATION[1], -1)):
    box_minmax(f'Corner_Guard_{y}', (HW - 0.012, min(y, y + sgn * 0.06), 0.11),
               (HW + 0.05, max(y, y + sgn * 0.06), 1.6), M('steel'), C_STAT, bevel=0.003)
# soffit sign on the corridor face of the lintel
text('Sign_Station_Soffit', "NURSES' STATION", 0.13, (HW - 0.008, (STATION[0] + STATION[1]) / 2, 2.62),
     (PI / 2, 0, -PI / 2), M('sign_text_dark'), C_STAT, extrude=0.004)

# ---------------------------------------------------------------- ceiling details
for k, yc in enumerate(LIGHT_YS):
    state = LIGHT_STATE.get(k, 'on')
    mat = {'on': M('light_on'), 'off': M('light_off'), 'flicker': M('light_flicker')}[state]
    box_minmax(f'Light_Frame_{k:02d}', (-0.31, yc - 0.61, H - 0.03), (0.31, yc + 0.61, H + 0.005),
               M('white_paint'), C_CEIL)
    box_minmax(f'Light_Diffuser_{k:02d}', (-0.27, yc - 0.57, H - 0.034), (0.27, yc + 0.57, H - 0.02),
               mat, C_CEIL)
    # sprinkler + smoke detector
    sx_ = 0.6 if k % 2 else -0.6
    cyl(f'Sprinkler_{k:02d}', 0.035, 0.012, (sx_, yc + 1.5, H - 0.006), M('chrome'), C_CEIL, seg=16)
    cyl(f'Sprinkler_Head_{k:02d}', 0.008, 0.04, (sx_, yc + 1.5, H - 0.03), M('chrome'), C_CEIL, seg=8)
    if k % 3 == 1:
        cyl(f'Smoke_Detector_{k:02d}', 0.07, 0.04, (0, yc + 1.5, H - 0.02), M('white_plastic'), C_CEIL,
            seg=24, bevel=0.01)
    if k % 2 == 0:
        vx = 0.9 if k % 4 == 0 else -0.9
        vy = yc + 1.5 + (0.3 if k % 4 == 0 else -0.3)
        box_minmax(f'Vent_Frame_{k:02d}', (vx - 0.29, vy - 0.29, H - 0.02), (vx + 0.29, vy + 0.29, H),
                   M('white_paint'), C_CEIL, bevel=0.005)
        for j in range(9):
            box_minmax(f'Vent_Slat_{k:02d}_{j}', (vx - 0.25, vy - 0.24 + j * 0.06, H - 0.025),
                       (vx + 0.25, vy - 0.23 + j * 0.06, H - 0.004), M('metal_dark'), C_CEIL)
for i, y in enumerate(BULKHEADS):
    box_minmax(f'Bulkhead_{i}', (-HW, y - 0.2, H - 0.32), (HW, y + 0.2, H + 0.01), M('ceiling_plain'), C_CEIL,
               bevel=0.01)

# ---------------------------------------------------------------- end wall + window
W_ = WINDOW
yw = Y1
box_minmax('EndWall_Bottom', (-HW - T, yw, 0), (HW + T, yw + W_['thick'], W_['z0']), M('wall'), C_WIN)
box_minmax('EndWall_Top', (-HW - T, yw, W_['z1']), (HW + T, yw + W_['thick'], H + 0.04), M('wall'), C_WIN)
box_minmax('EndWall_Left', (-HW - T, yw, W_['z0']), (W_['x0'], yw + W_['thick'], W_['z1']), M('wall'), C_WIN)
box_minmax('EndWall_Right', (W_['x1'], yw, W_['z0']), (HW + T, yw + W_['thick'], W_['z1']), M('wall'), C_WIN)
box_minmax('EndWall_Skirting', (-HW, yw - 0.012, 0), (HW, yw, 0.11), M('skirting'), C_WIN)
box_minmax('EndWall_Panel', (-HW, yw - 0.006, 0.11), (HW, yw, W_['z0'] - 0.04), M('wall_lower'), C_WIN)
box_minmax('Window_Sill', (W_['x0'] - 0.08, yw - 0.06, W_['z0'] - 0.03), (W_['x1'] + 0.08, yw + 0.05, W_['z0'] + 0.005),
           M('counter_top'), C_WIN, bevel=0.008)
gy = yw + W_['thick'] * 0.55
fw = 0.055
for name, mn, mx in (
        ('Frame_L', (W_['x0'], gy - 0.04, W_['z0']), (W_['x0'] + fw, gy + 0.04, W_['z1'])),
        ('Frame_R', (W_['x1'] - fw, gy - 0.04, W_['z0']), (W_['x1'], gy + 0.04, W_['z1'])),
        ('Frame_B', (W_['x0'], gy - 0.04, W_['z0']), (W_['x1'], gy + 0.04, W_['z0'] + fw)),
        ('Frame_T', (W_['x0'], gy - 0.04, W_['z1'] - fw), (W_['x1'], gy + 0.04, W_['z1'])),
        ('Frame_Mullion', (-0.03, gy - 0.034, W_['z0']), (0.03, gy + 0.034, W_['z1'])),   # recessed: no coplanar faces
        ('Frame_Transom', (W_['x0'] + 0.03, gy - 0.034, 2.02), (W_['x1'] - 0.03, gy + 0.034, 2.07))):
    box_minmax('Window_' + name, mn, mx, M('alu'), C_WIN, bevel=0.006)
g = box_minmax('Window_Glass', (W_['x0'], gy - 0.003, W_['z0']), (W_['x1'], gy + 0.003, W_['z1']), M('glass'), C_WIN)
g.visible_shadow = False
# venetian blinds over the upper part, slats share one mesh
by = yw - 0.035
box_minmax('Blind_Headrail', (W_['x0'] + 0.02, by - 0.025, W_['z1'] - 0.05), (W_['x1'] - 0.02, by + 0.025, W_['z1'] - 0.005),
           M('white_paint'), C_WIN, bevel=0.005)
slat = box('Blind_Slat_000', (W_['x1'] - W_['x0'] - 0.06, 0.028, 0.0015), (0, by, W_['z1'] - 0.07),
           M('white_plastic'), C_WIN, rot=(-38 * D2R, 0, 0))
z = W_['z1'] - 0.07
i = 1
while z > 1.72:
    z -= 0.024
    s = bpy.data.objects.new(f'Blind_Slat_{i:03d}', slat.data)
    C_WIN.objects.link(s)
    s.location = (0, by, z)
    s.rotation_euler = (-38 * D2R, 0, 0)
    i += 1
box_minmax('Blind_Bottomrail', (W_['x0'] + 0.03, by - 0.016, z - 0.025), (W_['x1'] - 0.03, by + 0.016, z - 0.01),
           M('white_paint'), C_WIN, bevel=0.004)
for x in (-0.9, 0.0, 0.9):
    cyl(f'Blind_Cord_{x}', 0.0012, W_['z1'] - z, (x + 0.05, by + 0.016, (W_['z1'] + z) / 2 - 0.02),
        M('white_plastic'), C_WIN, seg=6)
cyl('Blind_Wand', 0.006, 0.7, (W_['x1'] - 0.12, by - 0.03, W_['z1'] - 0.42), M('white_plastic'), C_WIN, seg=8)

# ---------------------------------------------------------------- exterior: dusk sky + city silhouette
sky = box_minmax('Sky_Backdrop', (-120, 140, -40), (120, 141, 70), M('sky'), C_OUT)
sky.visible_shadow = False
box_minmax('Ground_Outside', (-120, Y1 + 0.3, -14), (120, 140, -13), M('ground'), C_OUT)
rnd = random.Random(11)
x = -60.0
while x < 60:
    w = rnd.uniform(5, 14)
    d = rnd.uniform(6, 14)
    yb = rnd.uniform(62, 85)
    top = rnd.uniform(-4.5, -0.8) + max(0, 1.0 - abs(x) * 0.05)
    b = box_minmax(f'City_Block_{x:+.0f}', (x, yb, -14), (x + w, yb + d, top), M('city'), C_OUT)
    x += w + rnd.uniform(0.5, 4)
x = -90.0
while x < 90:
    w = rnd.uniform(8, 20)
    top = rnd.uniform(-2.5, 1.2)
    box_minmax(f'City_Far_{x:+.0f}', (x, 110, -14), (x + w, 116, top), M('city_far'), C_OUT)
    x += w + rnd.uniform(0, 3)
# a nearer hospital wing across the courtyard
box_minmax('Hospital_Wing_Opposite', (-26, 44, -14), (-6, 56, -0.6), M('city'), C_OUT)

print('architecture ok', len(bpy.data.objects))
