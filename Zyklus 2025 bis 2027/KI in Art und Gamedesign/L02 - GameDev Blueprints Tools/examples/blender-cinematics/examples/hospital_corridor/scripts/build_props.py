"""Step 3: place doors, rooms, nurse station, corridor props and signage."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # __file__ is injected by bl_client.py / build_all_bg.py
import bpy
import lib, layout
from lib import (box, box_minmax, cyl, sphere, torus, tube, rods, text, poly_prism, get_coll, instance,
                 empty, M, D2R, PI)
from layout import *

TP = lambda n: bpy.data.collections['T_' + n]
C_DOORS = get_coll('02_Doors_Rooms')
C_STATION = get_coll('03_Nurse_Station')
C_PROPS = get_coll('04_Corridor_Props')
C_SIGNS = get_coll('05_Signage')
rnd = random.Random(21)

# ---------------------------------------------------------------- doors + rooms
for side, y, state, num, lit in DOORS:
    sx = side_sign(side)
    e = empty(f'Door_{num}', C_DOORS, (sx * HW, y, 0))
    e.scale = (sx, 1, 1)
    if state == 'closed':
        f = instance(f'Door_{num}_Frame', TP('Door_Frame_Closed'), C_DOORS)
        leaf = instance(f'Door_{num}_Leaf', TP('Door_Leaf_Lit' if lit else 'Door_Leaf_Dark'), C_DOORS,
                        (-0.012, -0.57, 0))
    else:
        f = instance(f'Door_{num}_Frame', TP('Door_Frame_Open'), C_DOORS)
        ang = -88 if state == 'open' else -42
        leaf = instance(f'Door_{num}_Leaf', TP('Door_Leaf_Clear'), C_DOORS, (T - 0.05, -0.57, 0),
                        (0, 0, ang * D2R))
        r = instance(f'Room_{num}', TP('Patient_Room'), C_DOORS)
        r.parent = e
    f.parent = e
    leaf.parent = e
    # room number plaque beside the door (not mirrored, so text reads correctly)
    py = y + OW / 2 + FRAME + 0.18
    x0, x1 = sorted((sx * HW, sx * (HW - 0.012)))
    box_minmax(f'Plaque_{num}', (x0, py - 0.11, 1.48), (x1, py + 0.11, 1.62), M('sign_panel'), C_SIGNS, bevel=0.003)
    text(f'Plaque_{num}_Text', num, 0.075, (sx * (HW - 0.016), py, 1.55), (PI / 2, 0, -sx * PI / 2),
         M('sign_text'), C_SIGNS, extrude=0.001)

# ---------------------------------------------------------------- nurse station
S0, S1 = STATION
XB = HW + STATION_DEPTH         # back wall face
cs = C_STATION
box_minmax('Station_Front', (1.70, 12.7, 0.0), (1.76, 15.6, 1.08), M('wood'), cs, bevel=0.008)
box_minmax('Station_Front_Band', (1.692, 12.7, 0.72), (1.70, 15.6, 0.8), M('frame_paint'), cs)
box_minmax('Station_Front_Kick', (1.695, 12.7, 0.0), (1.70, 15.6, 0.1), M('skirting'), cs)
box_minmax('Station_End', (1.70, 15.6, 0.0), (2.5, 15.65, 1.08), M('wood'), cs, bevel=0.008)
box_minmax('Station_Ledge', (1.6, 12.66, 1.08), (2.0, 15.69, 1.115), M('counter_top'), cs, bevel=0.01)
box_minmax('Station_Desk', (1.76, 12.7, 0.72), (2.5, 15.6, 0.75), M('counter_top'), cs, bevel=0.006)
for y in (12.75, 14.15, 15.55):
    box_minmax(f'Station_Desk_Leg_{y}', (2.35, y - 0.02, 0), (2.45, y + 0.02, 0.72), M('metal_dark'), cs)
# glowing LED strip under the ledge (practical light)
box_minmax('Station_LED', (1.62, 12.7, 1.075), (1.66, 15.65, 1.08), M('light_warm'), cs)
# monitors, keyboards, phone, paperwork
for i, y in enumerate((13.2, 14.6)):
    rot = (0, 0, PI + (0.25 if i == 0 else -0.2))
    box(f'Monitor_{i}', (0.03, 0.55, 0.34), (2.2, y, 1.0), M('black_plastic'), cs, rot=rot, bevel=0.008)
    box(f'Monitor_{i}_Screen', (0.003, 0.52, 0.31), (2.219, y, 1.0), M('screen_ui'), cs, rot=rot)
    cyl(f'Monitor_{i}_Stand', 0.015, 0.12, (2.24, y, 0.81), M('black_plastic'), cs, seg=10)
    box(f'Monitor_{i}_Base', (0.18, 0.2, 0.012), (2.25, y, 0.756), M('black_plastic'), cs, bevel=0.004)
    box(f'Keyboard_{i}', (0.15, 0.44, 0.02), (2.4, y, 0.76), M('grey_plastic'), cs, rot=(0, 0, rot[2] - PI),
        bevel=0.004)
box_minmax('Phone', (2.2, 13.9, 0.75), (2.38, 14.12, 0.81), M('black_plastic'), cs, bevel=0.012)
for k in range(5):
    box(f'Chart_{k}', (0.24, 0.32, 0.012), (1.95 + rnd.uniform(-0.05, 0.05), 15.15 + rnd.uniform(-0.05, 0.05),
        0.756 + k * 0.013), [M('paper_white'), M('binder_b'), M('paper_white'), M('paper_yellow'), M('binder_r')][k],
        cs, rot=(0, 0, rnd.uniform(-0.2, 0.2)))
cyl('Mug', 0.04, 0.1, (2.35, 12.95, 0.75), M('white_paint'), cs, base=True, seg=16)
# desk lamp (warm practical)
cyl('Lamp_Base', 0.07, 0.02, (2.3, 12.85, 0.75), M('black_plastic'), cs, base=True, seg=20)
rods('Lamp_Arm', [((2.3, 12.85, 0.77), (2.38, 12.9, 1.15)), ((2.38, 12.9, 1.15), (2.22, 13.0, 1.28))], 0.008,
     M('black_plastic'), cs)
cyl('Lamp_Shade', 0.07, 0.12, (2.22, 13.0, 1.24), M('black_plastic'), cs, r2=0.035, seg=20, cap=False)
sphere('Lamp_Bulb', 0.025, (2.22, 13.0, 1.2), M('light_warm'), cs, seg=12)
ld = bpy.data.lights.new('Station_DeskLamp', 'POINT')
ld.energy = 12; ld.color = (1.0, 0.7, 0.42); ld.shadow_soft_size = 0.03
lib.new_obj('Station_DeskLamp', ld, cs, (2.22, 13.0, 1.19))
# back wall: patient whiteboard, cabinets, binders
box_minmax('Whiteboard_Frame', (XB - 0.025, 13.15, 1.0), (XB, 14.95, 2.0), M('alu'), cs, bevel=0.005)
box_minmax('Whiteboard', (XB - 0.028, 13.18, 1.03), (XB - 0.02, 14.92, 1.97), M('whiteboard'), cs)
for k in range(7):
    z = 1.08 + k * 0.125
    box_minmax(f'WB_Line_{k}', (XB - 0.031, 13.25, z), (XB - 0.028, 14.85, z + 0.004), M('marker'), cs)
    for j in range(rnd.randint(2, 5)):
        y0 = 13.3 + j * 0.3 + rnd.uniform(0, 0.06)
        box_minmax(f'WB_Note_{k}_{j}', (XB - 0.031, y0, z + 0.03), (XB - 0.0285, y0 + rnd.uniform(0.12, 0.28), z + 0.075),
                   rnd.choice([M('marker'), M('red'), M('binder_g')]), cs)
box_minmax('Upper_Cabinet', (XB - 0.35, 15.0, 1.6), (XB, 16.45, 2.4), M('wood'), cs, bevel=0.01)
box_minmax('Under_Cab_Glow', (XB - 0.3, 15.05, 1.595), (XB - 0.26, 16.4, 1.6), M('light_warm'), cs)
box_minmax('Lower_Cabinet', (XB - 0.6, 15.0, 0.0), (XB, 16.45, 0.9), M('wood'), cs, bevel=0.01)
box_minmax('Lower_Cabinet_Top', (XB - 0.62, 14.98, 0.9), (XB, 16.47, 0.93), M('counter_top'), cs, bevel=0.005)
bm = [M('binder_r'), M('binder_b'), M('binder_g'), M('binder_k'), M('binder_b')]
yy = 15.05
k = 0
while yy < 16.35:
    w = rnd.uniform(0.04, 0.07)
    h = rnd.uniform(0.26, 0.31)
    box(f'Binder_{k}', (0.26, w - 0.004, h), (XB - 0.45, yy + w / 2, 0.93 + h / 2), rnd.choice(bm), cs,
        rot=(rnd.uniform(-0.05, 0.05), 0, 0), bevel=0.003)
    yy += w
    k += 1
box_minmax('Printer', (XB - 0.5, 15.1, 0.93), (XB - 0.1, 15.5, 1.15), M('white_plastic'), cs, bevel=0.015)
box_minmax('Filing_Cabinet', (XB - 0.5, 12.6, 0.0), (XB, 13.05, 1.3), M('metal_dark'), cs, bevel=0.008)
for k in range(4):
    box_minmax(f'Filing_Drawer_{k}', (XB - 0.505, 12.62, 0.05 + k * 0.31), (XB - 0.49, 13.03, 0.33 + k * 0.31),
               M('metal_dark'), cs, bevel=0.004)
instance('Station_Clock', TP('Wall_Clock'), cs, (3.0, S1, 2.25))
instance('Station_Noticeboard', TP('Noticeboard_B'), cs, (3.6, S1, 1.45))
instance('Station_Sanitizer', TP('Sanitizer'), cs, (2.2, S1, 1.3))


def office_chair(name, loc, ang):
    e = empty(name, cs, loc, (0, 0, ang))
    segs = []
    for k in range(5):
        a = 2 * PI * k / 5
        segs.append(((0, 0, 0.08), (0.3 * math.cos(a), 0.3 * math.sin(a), 0.05)))
        cyl(f'{name}_Cw{k}', 0.025, 0.02, (0.3 * math.cos(a), 0.3 * math.sin(a), 0.025), M('black_plastic'), cs,
            rot=(PI / 2, 0, a), seg=12, parent=e)
    rods(f'{name}_Base', segs, 0.018, M('black_plastic'), cs, parent=e)
    cyl(f'{name}_Lift', 0.025, 0.36, (0, 0, 0.08), M('chrome'), cs, base=True, seg=14, parent=e)
    box(f'{name}_Seat', (0.48, 0.48, 0.08), (0, 0, 0.48), M('vinyl_seat'), cs, bevel=0.03, segs=3, parent=e)
    box(f'{name}_Back', (0.07, 0.45, 0.5), (0.27, 0, 0.85), M('vinyl_seat'), cs, rot=(0, -0.12, 0), bevel=0.03,
        segs=3, parent=e)
    rods(f'{name}_Spine', [((0.2, 0, 0.47), (0.28, 0, 0.62))], 0.02, M('black_plastic'), cs, parent=e)


office_chair('Station_Chair_A', (2.75, 13.35, 0), 0.3)
office_chair('Station_Chair_B', (2.85, 14.8, 0), -0.5)
# warm ceiling light over the station
for i, y in enumerate((13.5, 15.3)):
    box_minmax(f'Station_Light_{i}', (2.3, y - 0.3, H - 0.03), (3.5, y + 0.3, H), M('light_warm'), cs)
ld = bpy.data.lights.new('Station_Ceiling_Light', 'AREA')
ld.shape = 'RECTANGLE'; ld.size = 1.2; ld.size_y = 2.6
ld.energy = 160; ld.color = (1.0, 0.82, 0.62)
lib.new_obj('Station_Ceiling_Light', ld, cs, (2.9, 14.4, H - 0.05))

# ---------------------------------------------------------------- corridor props
cp = C_PROPS
def place(name, tmpl, loc, ang=0.0):
    return instance(name, TP(tmpl), cp, loc, (0, 0, ang))


RAIL_CLEAR = HW - 0.105 - 0.015      # inner face of the handrail minus 1.5 cm air gap
_PTS = {}


def tmpl_points(tmpl):
    """Template vertices in template space (curves: control points padded by their bevel radius)."""
    if tmpl not in _PTS:
        from mathutils import Matrix, Vector
        pts = []
        for o in TP(tmpl).all_objects:
            m = Matrix.LocRotScale(o.location, o.rotation_euler, o.scale)
            if o.type == 'MESH':
                pts += [m @ v.co for v in o.data.vertices]
            elif o.type == 'CURVE':
                r = o.data.bevel_depth
                for sp in o.data.splines:
                    for q in sp.points:
                        c = m @ Vector(q.co[:3])
                        pts += [c + Vector((dx, dy, 0)) for dx in (-r, r) for dy in (-r, r)]
        _PTS[tmpl] = pts
    return _PTS[tmpl]


def place_wall(name, tmpl, side, y, ang=0.0):
    """Park a floor prop along a side wall so its real footprint clears the handrail."""
    c, s_ = math.cos(ang), math.sin(ang)
    xs = [q.x * c - q.y * s_ for q in tmpl_points(tmpl)]
    sx = side_sign(side)
    reach = max(xs) if sx > 0 else -min(xs)
    return place(name, tmpl, (sx * (RAIL_CLEAR - reach), y, 0), ang)


place_wall('Wheelchair_A', 'Wheelchair', 'L', 7.1, -78 * D2R)
place_wall('Wheelchair_B', 'Wheelchair', 'R', 22.7, -110 * D2R)
place_wall('Wheelchair_C', 'Wheelchair', 'L', 28.7, -60 * D2R)
place_wall('Oxygen_Cart_A', 'Oxygen_Cart', 'R', 5.3, PI + 0.08)
place_wall('Oxygen_Rack_A', 'Oxygen_Rack', 'R', 21.1, PI)
place_wall('Spare_Bed_A', 'Bed_Spare', 'L', 13.1, 0.02)
place_wall('Spare_Bed_B', 'Bed_Made', 'L', 24.5, PI - 0.03)
place_wall('Crash_Cart', 'Crash_Cart', 'R', 17.55, -PI / 2 + 0.05)
place_wall('Med_Cart', 'Med_Cart', 'R', 26.9, -PI / 2)
place_wall('Supply_Trolley', 'Supply_Trolley', 'L', 17.9, PI / 2 + 0.04)
place_wall('IV_Pole_A', 'IV_Pole', 'L', 19.2, 0.4)
place_wall('IV_Pole_B', 'IV_Pole', 'R', 9.0, 1.2)
place_wall('Vitals_Stand', 'Vitals_Stand', 'R', 10.9, 2.6)
place('Wet_Floor_Sign', 'Wet_Floor_Sign', (-0.35, 19.7, 0), 0.35)
for i, y in enumerate((31.2, 31.78, 32.36)):
    place_wall(f'Waiting_Chair_{i}', 'Waiting_Chair', 'L', y, PI / 2)
box_minmax('Side_Table', (-1.45, 32.75, 0), (-0.95, 33.25, 0.45), M('wood'), cp, bevel=0.01)
for k in range(3):
    box(f'Magazine_{k}', (0.2, 0.28, 0.006), (-1.2 + k * 0.03, 33.0 - k * 0.02, 0.453 + k * 0.006),
        [M('paper_blue'), M('paper_pink'), M('paper_white')][k], cp, rot=(0, 0, 0.3 * k - 0.2))
place_wall('Plant_End', 'Plant', 'R', 33.15)
place_wall('Plant_Station', 'Plant', 'R', 12.0, 1.0)
# wall-mounted items (template faces -Y; rotate to face into the corridor)
RW, LW = -PI / 2, PI / 2
place('Noticeboard_A', 'Noticeboard', (HW, 3.4, 1.55), RW)
place('Noticeboard_End', 'Noticeboard_B', (HW, 31.7, 1.55), RW)
place('Sanitizer_A', 'Sanitizer', (-HW, 3.0, 1.35), LW)
place('Sanitizer_B', 'Sanitizer', (HW, 8.75, 1.35), RW)
place('Sanitizer_C', 'Sanitizer', (-HW, 11.2, 1.35), LW)
place('Sanitizer_D', 'Sanitizer', (HW, 23.1, 1.35), RW)
place('Extinguisher_A', 'Extinguisher', (-HW, 6.2, 0.45), LW)   # clears the handrail top
place('Extinguisher_B', 'Extinguisher', (HW, 28.2, 0.45), RW)


# ---------------------------------------------------------------- hanging signage
def hanging_sign(name, y, lines, w=1.4, h=0.32, z_top=2.62, panel=None, txt=None, arrow=None, x=0.0):
    panel = panel or M('sign_panel')
    txt = txt or M('sign_text')
    d = 0.035
    zc = z_top - h / 2
    box_minmax(name + '_Panel', (x - w / 2, y - d / 2, z_top - h), (x + w / 2, y + d / 2, z_top), panel, C_SIGNS, bevel=0.008)
    rods(name + '_Rods', [((x - w / 2 + 0.12, y, z_top), (x - w / 2 + 0.12, y, H)), ((x + w / 2 - 0.12, y, z_top), (x + w / 2 - 0.12, y, H))],
         0.004, M('steel'), C_SIGNS, seg=6)
    dirx = 0 if not arrow else (1 if arrow == 'R' else -1)
    for sgn, rz in ((-1, 0.0), (1, PI)):
        yy = y + sgn * (d / 2 + 0.004)
        n = len(lines)
        for i, (body, size) in enumerate(lines):
            z = zc + (n - 1) * 0.055 - i * 0.11
            text(f'{name}_T{i}_{sgn}', body, size, (x - 0.09 * dirx, yy, z), (PI / 2, 0, rz), txt, C_SIGNS,
                 extrude=0.001)
        if arrow:
            pts = [(-0.07, 0.025), (0.02, 0.025), (0.02, 0.06), (0.08, 0.0), (0.02, -0.06), (0.02, -0.025),
                   (-0.07, -0.025)]
            ar = poly_prism(f'{name}_Arrow_{sgn}', pts, 0.002, txt, C_SIGNS)
            ar.location = (x + dirx * (w / 2 - 0.16), yy + sgn * 0.002, zc)   # both prism faces ≥ 4 mm off the panel
            ar.rotation_euler = (PI / 2, 0, 0 if dirx > 0 else PI)


hanging_sign('Sign_Ward', 8.6, [('WARD 4B  -  CARDIOLOGY', 0.085), ('ROOMS 401 - 412', 0.06)], w=1.5)
hanging_sign('Sign_Station', 12.1, [("NURSES' STATION", 0.08)], w=1.2, h=0.2, arrow='R', x=0.62, z_top=2.5)
hanging_sign('Sign_Radiology', 25.8, [('RADIOLOGY  /  LIFTS', 0.075)], w=1.3, h=0.22, arrow='L', x=-0.55)
# green EXIT sign
ey = 30.6
box_minmax('Exit_Sign_Box', (-0.25, ey - 0.04, 2.38), (0.25, ey + 0.04, 2.6), M('white_paint'), C_SIGNS, bevel=0.006)
for sgn in (-1, 1):
    box_minmax(f'Exit_Sign_Face_{sgn}', (-0.23, min(ey + sgn * 0.04, ey + sgn * 0.046), 2.40),
               (0.23, max(ey + sgn * 0.04, ey + sgn * 0.046), 2.58), M('exit_green'), C_SIGNS)
    text(f'Exit_Sign_Text_{sgn}', 'EXIT', 0.11, (0.0, ey + sgn * 0.05, 2.49), (PI / 2, 0, 0 if sgn < 0 else PI),
         M('sign_text'), C_SIGNS)
rods('Exit_Sign_Rods', [((-0.15, ey, 2.6), (-0.15, ey, H)), ((0.15, ey, 2.6), (0.15, ey, H))], 0.004, M('steel'),
     C_SIGNS, seg=6)
ld = bpy.data.lights.new('Exit_Sign_Glow', 'POINT')
ld.energy = 3; ld.color = (0.2, 1.0, 0.4); ld.shadow_soft_size = 0.2
lib.new_obj('Exit_Sign_Glow', ld, C_SIGNS, (0, ey - 0.15, 2.45))

print('props ok', len(bpy.data.objects))
