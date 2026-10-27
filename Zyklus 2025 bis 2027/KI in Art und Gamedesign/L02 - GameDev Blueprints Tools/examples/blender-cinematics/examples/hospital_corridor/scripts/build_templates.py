"""Step 2: reusable prop templates. Each template lives in its own collection under
_Templates (excluded from the view layer) and is placed with collection instances."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # __file__ is injected by bl_client.py / build_all_bg.py
import bpy
import lib, layout
from lib import (box, box_minmax, cyl, sphere, torus, tube, rods, text, poly_prism, get_coll,
                 panel_grid, M, D2R, PI)
from mathutils import Vector

C_T = get_coll('_Templates')
rnd = random.Random(7)


def T(name):
    return get_coll('T_' + name, C_T)


# =============================================================== doors
def door_frame(name, open_):
    c = T(name)
    hw = layout.OW / 2
    f = layout.FRAME
    x0, x1 = (-0.025, layout.T + 0.02) if open_ else (-0.025, 0.02)
    # the lining must sit proud of the wall reveal (ins), never coplanar with it, or it z-fights
    ins = 0.008 if open_ else 0.0
    # butt joint: jambs stop under the head, so frame pieces only touch along edges (no overlapping coplanar faces)
    box_minmax(name + '_JambA', (x0, -hw - f, 0), (x1, -hw + ins, layout.OH - ins), M('frame_paint'), c, bevel=0.006)
    box_minmax(name + '_JambB', (x0, hw - ins, 0), (x1, hw + f, layout.OH - ins), M('frame_paint'), c, bevel=0.006)
    box_minmax(name + '_Head', (x0, -hw - f, layout.OH - ins), (x1, hw + f, layout.OH + f), M('frame_paint'), c,
               bevel=0.006)
    if open_:
        # door stop strip inside the lining
        box_minmax(name + '_Stop', (layout.T - 0.02, -hw, layout.OH - 0.015), (layout.T + 0.014, hw, layout.OH),
                   M('frame_paint'), c)
    return c


def door_leaf(name, glass_mat):
    """Origin on the hinge axis, leaf extends +Y, thickness +X."""
    c = T(name)
    W, Hh, t = 1.14, 2.17, 0.045
    gy0, gy1, gz0, gz1 = 0.66, 0.86, 1.15, 1.85
    wood = M('wood')
    box_minmax(name + '_Bottom', (0, 0, 0.01), (t, W, gz0), wood, c)
    box_minmax(name + '_Top', (0, 0, gz1), (t, W, Hh), wood, c)
    box_minmax(name + '_Hinge', (0, 0, gz0), (t, gy0, gz1), wood, c)
    box_minmax(name + '_Latch', (0, gy1, gz0), (t, W, gz1), wood, c)
    b = 0.014
    for sx in (-0.004, t + 0.004):
        for k, (mn, mx) in enumerate((((gy0 - b, gz0 - b), (gy1 + b, gz0)), ((gy0 - b, gz1), (gy1 + b, gz1 + b)),
                                      ((gy0 - b, gz0), (gy0, gz1)), ((gy1, gz0), (gy1 + b, gz1)))):
            box_minmax(name + f'_Bead_{sx:.2f}_{k}', (sx - 0.005, mn[0], mn[1]), (sx + 0.005, mx[0], mx[1]),
                       M('steel'), c, bevel=0.002)
    g = box_minmax(name + '_Glass', (t / 2 - 0.004, gy0, gz0), (t / 2 + 0.004, gy1, gz1), glass_mat, c)
    if glass_mat == M('glass'):
        g.visible_shadow = False
    for sx, sgn in ((-0.002, -1), (t + 0.002, 1)):
        box_minmax(name + f'_Kick_{sgn}', (min(sx, sx + sgn * 0.002), 0.03, 0.02),
                   (max(sx, sx + sgn * 0.002), W - 0.03, 0.27), M('steel'), c)
        # lever handle
        hx = sx + sgn * 0.03
        rods(name + f'_Lever_{sgn}', [((sx, W - 0.08, 1.02), (hx, W - 0.08, 1.02)),
                                       ((hx, W - 0.08, 1.02), (hx, W - 0.22, 1.02))], 0.009, M('chrome'), c)
        cyl(name + f'_Rose_{sgn}', 0.026, 0.01, (sx + sgn * 0.004, W - 0.08, 1.02), M('chrome'), c,
            rot=(0, PI / 2, 0), seg=20)
        box_minmax(name + f'_Push_{sgn}', (min(sx, sx + sgn * 0.002), W - 0.13, 1.2),
                   (max(sx, sx + sgn * 0.002), W - 0.03, 1.5), M('steel'), c)
    return c


door_frame('Door_Frame_Open', True)
door_frame('Door_Frame_Closed', False)
door_leaf('Door_Leaf_Lit', M('glass_frosted'))
door_leaf('Door_Leaf_Dark', M('glass_dark'))
door_leaf('Door_Leaf_Clear', M('glass'))


# =============================================================== hospital bed
def caster(name, c, x, y, r=0.055, z_top=0.2):
    cyl(name + '_Wheel', r, 0.035, (x, y, r + 0.003), M('grey_plastic'), c, rot=(0, PI / 2, 0), seg=20, bevel=0.008)
    cyl(name + '_Hub', r * 0.45, 0.045, (x, y, r + 0.003), M('steel'), c, rot=(0, PI / 2, 0), seg=12)
    box_minmax(name + '_Fork', (x - 0.03, y - 0.03, r + 0.003), (x + 0.03, y + 0.03, r * 2 + 0.03),
               M('metal_dark'), c, bevel=0.006)
    cyl(name + '_Stem', 0.012, z_top - (r * 2 + 0.03), (x, y, (z_top + r * 2 + 0.03) / 2), M('steel'), c, seg=10)


def bed(name, made=True, head_angle=28, rail_down=False):
    c = T(name)
    L, Wd = 2.0, 0.9
    caster(name + '_C1', c, 0.36, 0.82, z_top=0.2)
    caster(name + '_C2', c, -0.36, 0.82, z_top=0.2)
    caster(name + '_C3', c, 0.36, -0.82, z_top=0.2)
    caster(name + '_C4', c, -0.36, -0.82, z_top=0.2)
    box_minmax(name + '_Chassis', (-0.4, -0.92, 0.18), (0.4, 0.92, 0.27), M('metal_dark'), c, bevel=0.02)
    box_minmax(name + '_Shroud', (-0.36, -0.75, 0.27), (0.36, 0.75, 0.33), M('white_plastic'), c, bevel=0.025)
    for y in (-0.5, 0.5):
        box_minmax(name + f'_Column_{y}', (-0.08, y - 0.08, 0.33), (0.08, y + 0.08, 0.46), M('grey_plastic'), c,
                   bevel=0.02)
    box_minmax(name + '_Deck', (-0.44, -L / 2, 0.46), (0.44, L / 2, 0.5), M('metal_dark'), c, bevel=0.01)
    mat_top = M('sheet') if made else M('mattress')
    # mattress: flat foot/seat section + raised head section
    hinge_y = 0.2
    box_minmax(name + '_Mattress_Foot', (-0.44, -0.98, 0.5), (0.44, hinge_y, 0.66), mat_top, c, bevel=0.045, segs=3)
    a = head_angle * D2R
    hl = 0.98 - hinge_y
    hm = box(name + '_Mattress_Head', (0.88, hl, 0.16), (0, hinge_y + hl / 2 * math.cos(a) - 0.0,
             0.58 + hl / 2 * math.sin(a)), mat_top, c, rot=(a, 0, 0), bevel=0.045, segs=3)
    # pillow on the head section
    pw = box(name + '_Pillow', (0.62, 0.4, 0.17), (0, hinge_y + 0.55 * math.cos(a), 0.66 + 0.07 + 0.55 * math.sin(a)),
             M('sheet'), c, rot=(a, 0, 0.03))
    pw.modifiers.new('Subsurf', 'SUBSURF').levels = 2
    pw.modifiers['Subsurf'].render_levels = 2
    pw.data.shade_smooth()
    if made:
        # blanket over the lower body with hanging side flaps
        bl0, bl1 = -1.0, 0.05
        # blanket stays inside the side rails (rail inner faces are at ±0.47)
        box_minmax(name + '_Blanket_Top', (-0.455, bl0, 0.66), (0.455, bl1, 0.69), M('blanket'), c, bevel=0.012)
        for sx in (-1, 1):
            x0, x1 = sorted((sx * 0.452, sx * 0.466))
            box_minmax(name + f'_Blanket_Flap_{sx}', (x0, bl0, 0.42), (x1, bl1, 0.686), M('blanket'), c, bevel=0.008)
        box_minmax(name + '_Sheet_Fold', (-0.465, bl1 - 0.12, 0.665), (0.465, bl1 + 0.02, 0.7), M('sheet'), c,
                   bevel=0.012)
    else:
        for i in range(3):
            box_minmax(name + f'_Linen_{i}', (-0.25, -0.88, 0.66 + i * 0.045), (0.25, -0.5, 0.7 + i * 0.045),
                       [M('sheet'), M('blanket'), M('sheet')][i], c, bevel=0.015)
    # head & foot boards
    for nm, y, zt in (('Head', 1.02, 1.0), ('Foot', -1.02, 0.88)):
        y0, y1 = sorted((y, y + (0.04 if y > 0 else -0.04)))
        box_minmax(name + f'_{nm}board', (-0.48, y0, 0.44), (0.48, y1, zt), M('beige_plastic'), c, bevel=0.03, segs=3)
        box_minmax(name + f'_{nm}board_Insert', (-0.38, y0 - 0.004, zt - 0.32), (0.38, y1 + 0.004, zt - 0.08),
                   M('wood'), c, bevel=0.01)
    box_minmax(name + '_Foot_Panel', (-0.2, -1.07, 0.62), (0.2, -1.06, 0.74), M('grey_plastic'), c, bevel=0.004)
    # side rails (split rails), one foot rail lowered optionally
    for sx in (-1, 1):
        x0, x1 = sorted((sx * 0.47, sx * 0.5))
        box_minmax(name + f'_Rail_Head_{sx}', (x0, 0.12, 0.66), (x1, 0.9, 0.98), M('white_plastic'), c, bevel=0.012)
        box_minmax(name + f'_Rail_Head_Win_{sx}', (x0 - 0.005, 0.25, 0.76), (x1 + 0.005, 0.75, 0.9),
                   M('grey_plastic'), c, bevel=0.01)
        zl = 0.44 if (rail_down and sx > 0) else 0.66
        box_minmax(name + f'_Rail_Foot_{sx}', (x0, -0.9, zl), (x1, -0.06, zl + 0.28), M('white_plastic'), c,
                   bevel=0.012)
    # handset control on a cable
    box_minmax(name + '_Handset', (0.5, 0.35, 0.72), (0.53, 0.42, 0.86), M('grey_plastic'), c, bevel=0.008)
    return c


bed('Bed_Made', True, 30)
bed('Bed_Spare', False, 12, rail_down=True)


# =============================================================== wheelchair (forward = +X)
def wheelchair(name):
    c = T(name)
    fr = []
    for sy in (-0.235, 0.235):
        side = [(0.27, sy, 0.2), (0.27, sy, 0.5), (-0.17, sy, 0.5), (-0.21, sy, 0.93), (-0.31, sy, 0.95)]
        tube(name + f'_Frame_{sy:+.2f}', side, 0.012, M('chrome'), c, fillet=0.04)
        tube(name + f'_Lower_{sy:+.2f}', [(0.27, sy, 0.22), (-0.14, sy, 0.22), (-0.17, sy, 0.5)], 0.011,
             M('chrome'), c, fillet=0.04)
        tube(name + f'_Arm_{sy:+.2f}', [(-0.15, sy, 0.5), (-0.15, sy, 0.73), (0.18, sy, 0.73), (0.2, sy, 0.5)],
             0.01, M('chrome'), c, fillet=0.03)
        box_minmax(name + f'_ArmPad_{sy:+.2f}', (-0.14, sy - 0.025, 0.73), (0.16, sy + 0.025, 0.76),
                   M('vinyl_seat'), c, bevel=0.01)
        tube(name + f'_Hanger_{sy:+.2f}', [(0.25, sy, 0.48), (0.4, sy * 0.85, 0.15)], 0.01, M('chrome'), c)
        box_minmax(name + f'_Footplate_{sy:+.2f}', (0.36, sy * 0.85 - (0.13 if sy > 0 else -0.02),
                   0.12), (0.5, sy * 0.85 + (0.02 if sy > 0 else 0.13), 0.135), M('black_plastic'), c, bevel=0.005)
        cyl(name + f'_Grip_{sy:+.2f}', 0.016, 0.1, (-0.33, sy, 0.952), M('rubber'), c, rot=(0, PI / 2 - 0.15, 0),
            seg=12)
        # rear wheel
        wy = sy * 1.2
        torus(name + f'_Tire_{sy:+.2f}', 0.285, 0.018, (-0.12, wy, 0.303), M('rubber'), c, rot=(PI / 2, 0, 0),
              seg=40)
        torus(name + f'_Rim_{sy:+.2f}', 0.265, 0.009, (-0.12, wy, 0.303), M('alu'), c, rot=(PI / 2, 0, 0), seg=40,
              rseg=6)
        torus(name + f'_PushRim_{sy:+.2f}', 0.255, 0.007, (-0.12, wy + (0.035 if sy > 0 else -0.035), 0.303),
              M('chrome'), c, rot=(PI / 2, 0, 0), seg=40, rseg=6)
        sp = []
        for k in range(18):
            a = 2 * PI * k / 18
            sp.append(((-0.12, wy, 0.303), (-0.12 + 0.262 * math.cos(a), wy + (0.01 if k % 2 else -0.01),
                                            0.303 + 0.262 * math.sin(a)), 0.0016))
        rods(name + f'_Spokes_{sy:+.2f}', sp, 0.0016, M('chrome'), c, seg=5)
        cyl(name + f'_Hub_{sy:+.2f}', 0.03, 0.06, (-0.12, wy, 0.303), M('alu'), c, rot=(PI / 2, 0, 0), seg=16)
        # front caster
        cyl(name + f'_Caster_{sy:+.2f}', 0.075, 0.028, (0.31, sy, 0.077), M('grey_plastic'), c, rot=(PI / 2, 0, 0),
            seg=20, bevel=0.006)
        rods(name + f'_Fork_{sy:+.2f}', [((0.31, sy - 0.022, 0.077), (0.28, sy - 0.022, 0.2)),
                                          ((0.31, sy + 0.022, 0.077), (0.28, sy + 0.022, 0.2)),
                                          ((0.28, sy - 0.022, 0.2), (0.28, sy + 0.022, 0.2))], 0.006, M('chrome'), c)
    rods(name + '_Cross', [((0.1, -0.235, 0.24), (-0.1, 0.235, 0.49)), ((0.1, 0.235, 0.24), (-0.1, -0.235, 0.49)),
                           ((-0.12, -0.36, 0.303), (-0.12, 0.36, 0.303), 0.008)], 0.01, M('chrome'), c)
    box(name + '_Seat', (0.42, 0.46, 0.02), (0.05, 0, 0.505), M('vinyl_seat'), c, bevel=0.008)
    box(name + '_Back', (0.02, 0.46, 0.36), (-0.195, 0, 0.73), M('vinyl_seat'), c, rot=(0, -0.08, 0), bevel=0.008)
    return c


wheelchair('Wheelchair')


# =============================================================== oxygen cylinders
def o2_cylinder(prefix, c, x, y, z=0.0, h=0.9, r=0.085):
    cyl(prefix + '_Body', r, h, (x, y, z + 0.02), M('green_tank'), c, seg=28, base=True, bevel=0.01)
    sphere(prefix + '_Shoulder', r, (x, y, z + 0.02 + h), M('white_paint'), c, scale=(1, 1, 0.55), seg=28)
    cyl(prefix + '_Neck', 0.025, 0.06, (x, y, z + h + 0.09), M('chrome'), c, seg=16)
    box(prefix + '_Valve', (0.045, 0.045, 0.06), (x, y, z + h + 0.14), M('chrome'), c, bevel=0.006)
    torus(prefix + '_Handwheel', 0.028, 0.006, (x, y, z + h + 0.18), M('black_plastic'), c, seg=16, rseg=6)
    cyl(prefix + '_Gauge', 0.03, 0.022, (x - 0.045, y, z + h + 0.14), M('chrome'), c, rot=(0, PI / 2, 0), seg=20)
    cyl(prefix + '_Gauge_Face', 0.025, 0.002, (x - 0.059, y, z + h + 0.14), M('gauge_face'), c,
        rot=(0, PI / 2, 0), seg=20)
    box(prefix + '_Tag', (0.002, 0.06, 0.09), (x - r - 0.004, y, z + h - 0.12), M('paper_white'), c)


def o2_cart(name):
    c = T(name)
    box_minmax(name + '_Base', (-0.12, -0.24, 0.06), (0.12, 0.24, 0.08), M('metal_dark'), c, bevel=0.005)
    for y in (-0.21, 0.21):
        cyl(name + f'_Wheel_{y}', 0.06, 0.03, (-0.08, y, 0.06), M('rubber'), c, rot=(PI / 2, 0, 0), seg=18)
    rods(name + '_Frame', [((-0.12, -0.2, 0.08), (-0.14, -0.2, 1.1)), ((-0.12, 0.2, 0.08), (-0.14, 0.2, 1.1)),
                           ((-0.14, -0.2, 1.1), (-0.14, 0.2, 1.1)), ((-0.13, -0.2, 0.55), (-0.13, 0.2, 0.55)),
                           ((-0.13, -0.2, 0.85), (-0.13, 0.2, 0.85))], 0.011, M('metal_dark'), c)
    torus(name + '_Ring_A', 0.09, 0.006, (0, -0.1, 0.85), M('metal_dark'), c, seg=24, rseg=6)
    torus(name + '_Ring_B', 0.09, 0.006, (0, 0.1, 0.85), M('metal_dark'), c, seg=24, rseg=6)
    o2_cylinder(name + '_CylA', c, 0, -0.1, 0.06)
    o2_cylinder(name + '_CylB', c, 0, 0.1, 0.06)
    return c


def o2_rack(name):
    c = T(name)
    box_minmax(name + '_Base', (-0.12, -0.33, 0.0), (0.12, 0.33, 0.03), M('metal_dark'), c, bevel=0.005)
    rods(name + '_Frame', [((-0.11, -0.32, 0.03), (-0.11, -0.32, 1.0)), ((-0.11, 0.32, 0.03), (-0.11, 0.32, 1.0)),
                           ((-0.11, -0.32, 0.95), (-0.11, 0.32, 0.95)), ((-0.11, -0.32, 0.5), (-0.11, 0.32, 0.5))],
         0.012, M('metal_dark'), c)
    for i, y in enumerate((-0.2, 0.0, 0.2)):
        o2_cylinder(name + f'_Cyl{i}', c, 0.0, y, 0.03, h=0.95 if i != 1 else 0.82)
    # restraint chain approximated by small links
    links = [((-0.1, -0.32 + k * 0.032, 0.72 + 0.012 * math.sin(k)), (-0.09, -0.3 + k * 0.032, 0.72), 0.004)
             for k in range(20)]
    rods(name + '_Chain', links, 0.004, M('steel'), c, seg=5)
    return c


o2_cart('Oxygen_Cart')
o2_rack('Oxygen_Rack')


# =============================================================== trolleys
def casters4(name, c, hx, hy):
    for i, (x, y) in enumerate(((hx, hy), (-hx, hy), (hx, -hy), (-hx, -hy))):
        cyl(name + f'_Cw{i}', 0.04, 0.025, (x, y, 0.045), M('grey_plastic'), c, rot=(PI / 2, 0, 0), seg=16)
        box_minmax(name + f'_Cf{i}', (x - 0.02, y - 0.02, 0.045), (x + 0.02, y + 0.02, 0.11), M('metal_dark'), c,
                   bevel=0.004)


def drawer_cart(name, body_mat, drawer_mat, w=0.75, d=0.5, h=0.95, drawers=(0.12, 0.12, 0.15, 0.18, 0.22),
                defib=False):
    c = T(name)
    casters4(name, c, w / 2 - 0.06, d / 2 - 0.06)
    z0 = 0.11
    box_minmax(name + '_Bumper', (-w / 2 - 0.02, -d / 2 - 0.02, z0), (w / 2 + 0.02, d / 2 + 0.02, z0 + 0.05),
               M('grey_plastic'), c, bevel=0.02)
    box_minmax(name + '_Body', (-w / 2, -d / 2, z0 + 0.05), (w / 2, d / 2, h), body_mat, c, bevel=0.015)
    z = h - 0.03
    for i, dh in enumerate(drawers):
        box_minmax(name + f'_Drawer_{i}', (-w / 2 + 0.03, -d / 2 - 0.012, z - dh + 0.008), (w / 2 - 0.03, -d / 2, z - 0.008),
                   drawer_mat, c, bevel=0.006)
        rods(name + f'_Pull_{i}', [((-0.12, -d / 2 - 0.03, z - 0.03), (0.12, -d / 2 - 0.03, z - 0.03))], 0.007,
             M('chrome'), c)
        z -= dh
    box_minmax(name + '_Top', (-w / 2 - 0.02, -d / 2 - 0.02, h), (w / 2 + 0.02, d / 2 + 0.02, h + 0.03),
               M('grey_plastic'), c, bevel=0.01)
    for sx in (-1, 1):
        x0, x1 = sorted((sx * (w / 2 + 0.02), sx * (w / 2 - 0.0)))
        box_minmax(name + f'_Rim_{sx}', (x0, -d / 2 - 0.02, h + 0.03), (x1, d / 2 + 0.02, h + 0.07),
                   M('grey_plastic'), c, bevel=0.008)
    rods(name + '_Handle', [((w / 2 + 0.02, -0.18, h - 0.05), (w / 2 + 0.07, -0.18, h - 0.05)),
                            ((w / 2 + 0.02, 0.18, h - 0.05), (w / 2 + 0.07, 0.18, h - 0.05)),
                            ((w / 2 + 0.07, -0.18, h - 0.05), (w / 2 + 0.07, 0.18, h - 0.05))], 0.012,
         M('chrome'), c)
    if defib:
        box_minmax(name + '_Defib', (-0.3, -0.12, h + 0.03), (0.08, 0.16, h + 0.3), M('grey_plastic'), c,
                   bevel=0.02)
        box_minmax(name + '_Defib_Screen', (-0.25, -0.125, h + 0.12), (-0.03, -0.12, h + 0.27), M('screen_ecg'), c)
        box_minmax(name + '_Defib_Band', (-0.3, -0.122, h + 0.04), (0.08, -0.118, h + 0.08), M('yellow'), c)
        cyl(name + '_Sharps', 0.07, 0.2, (0.22, 0.05, h + 0.03), M('yellow'), c, base=True, seg=16)
        cyl(name + '_Sharps_Lid', 0.072, 0.03, (0.22, 0.05, h + 0.23), M('red'), c, base=True, seg=16)
        box_minmax(name + '_Glovebox', (0.12, -0.2, h + 0.03), (0.3, -0.08, h + 0.12), M('paper_blue'), c)
    else:
        for i in range(3):
            box_minmax(name + f'_Supplies_{i}', (-0.3 + i * 0.2, -0.15, h + 0.03), (-0.14 + i * 0.2, 0.12, h + 0.03 + 0.06 + 0.03 * i),
                       [M('paper_white'), M('paper_blue'), M('white_plastic')][i], c, bevel=0.005)
    return c


drawer_cart('Crash_Cart', M('red'), M('red'), defib=True)
drawer_cart('Med_Cart', M('white_plastic'), M('blue'), w=0.6, d=0.48, h=1.0,
            drawers=(0.08, 0.08, 0.08, 0.08, 0.15, 0.15, 0.2))


def supply_trolley(name):
    c = T(name)
    w, d = 0.9, 0.5
    casters4(name, c, w / 2 - 0.04, d / 2 - 0.04)
    posts = [((x, y, 0.11), (x, y, 1.0)) for x in (-w / 2, w / 2) for y in (-d / 2, d / 2)]
    rods(name + '_Posts', posts, 0.013, M('steel'), c)
    for i, z in enumerate((0.2, 0.55, 0.9)):
        box_minmax(name + f'_Shelf_{i}', (-w / 2, -d / 2, z), (w / 2, d / 2, z + 0.02), M('steel'), c, bevel=0.004)
        for sx in (-1, 1):
            box_minmax(name + f'_Lip_{i}_{sx}', (-w / 2, sx * d / 2 - 0.006, z - 0.005), (w / 2, sx * d / 2 + 0.006, z + 0.04),
                       M('steel'), c)
    for j, x in enumerate((-0.3, 0.0, 0.3)):
        for i, z in enumerate((0.57, 0.92)):
            b = box_minmax(name + f'_Bin_{i}_{j}', (x - 0.13, -0.2, z), (x + 0.13, 0.2, z + 0.14),
                           [M('blue'), M('blue'), M('yellow')][(i + j) % 3 if (i + j) % 4 else 0], c, bevel=0.012)
    for k in range(4):
        box_minmax(name + f'_Linen_{k}', (-0.4, -0.22, 0.22 + k * 0.06), (0.4, 0.22, 0.27 + k * 0.06),
                   [M('sheet'), M('blanket')][k % 2], c, bevel=0.02)
    rods(name + '_Handle', [((-w / 2 - 0.06, -0.18, 1.0), (-w / 2 - 0.06, 0.18, 1.0)),
                            ((-w / 2, -0.18, 1.0), (-w / 2 - 0.06, -0.18, 1.0)),
                            ((-w / 2, 0.18, 1.0), (-w / 2 - 0.06, 0.18, 1.0))], 0.012, M('steel'), c)
    return c


supply_trolley('Supply_Trolley')


# =============================================================== IV pole, vitals stand
def star_base(name, c, r=0.3, z=0.1, legs=5):
    segs = []
    for k in range(legs):
        a = 2 * PI * k / legs
        p = (r * math.cos(a), r * math.sin(a), z - 0.03)
        segs.append(((0, 0, z), p))
        cyl(name + f'_Cw{k}', 0.03, 0.02, (p[0], p[1], 0.03), M('grey_plastic'), c, rot=(PI / 2, 0, a), seg=14)
    rods(name + '_Legs', segs, 0.014, M('chrome'), c)


def iv_pole(name):
    c = T(name)
    star_base(name, c)
    cyl(name + '_Pole', 0.012, 1.95, (0, 0, 0.08), M('chrome'), c, base=True, seg=12)
    hooks = []
    for k in range(4):
        a = PI / 4 + k * PI / 2
        e = (0.12 * math.cos(a), 0.12 * math.sin(a), 2.0)
        hooks.append(((0, 0, 2.0), e, 0.006))
        hooks.append((e, (e[0] * 1.05, e[1] * 1.05, 2.05), 0.006))
    rods(name + '_Hooks', hooks, 0.006, M('chrome'), c)
    sphere(name + '_Bag', 1.0, (0.12, 0.0, 1.86), M('iv_bag'), c, scale=(0.02, 0.07, 0.11), seg=16).visible_shadow = False
    box(name + '_Bag_Label', (0.002, 0.07, 0.06), (0.141, 0.0, 1.86), M('paper_white'), c)
    cyl(name + '_Drip', 0.009, 0.06, (0.12, 0, 1.71), M('iv_bag'), c, seg=10).visible_shadow = False
    tube(name + '_Line', [(0.12, 0, 1.68), (0.14, 0.02, 1.4), (0.08, 0.06, 1.15), (0.02, 0.04, 1.08)], 0.002,
         M('iv_bag'), c).visible_shadow = False
    box_minmax(name + '_Pump', (0.012, -0.08, 1.0), (0.13, 0.08, 1.18), M('white_plastic'), c, bevel=0.012)
    box_minmax(name + '_Pump_Screen', (0.131, -0.05, 1.11), (0.133, 0.05, 1.16), M('screen_ui'), c)
    box_minmax(name + '_Clamp', (-0.03, -0.03, 1.06), (0.015, 0.03, 1.12), M('metal_dark'), c, bevel=0.005)
    return c


iv_pole('IV_Pole')


def vitals_stand(name):
    c = T(name)
    star_base(name, c, 0.28)
    cyl(name + '_Pole', 0.018, 1.2, (0, 0, 0.08), M('alu'), c, base=True, seg=14)
    box_minmax(name + '_Basket', (-0.15, -0.1, 0.85), (0.15, 0.1, 0.95), M('grey_plastic'), c, bevel=0.01)
    box(name + '_Head', (0.1, 0.3, 0.24), (0.0, 0, 1.38), M('white_plastic'), c, rot=(0, 0.15, 0), bevel=0.02)
    box(name + '_Screen', (0.005, 0.24, 0.17), (0.052, 0, 1.39), M('screen_ecg'), c, rot=(0, 0.15, 0))
    tube(name + '_Cuff_Hose', [(0.04, 0.12, 1.3), (0.15, 0.2, 1.0), (0.1, 0.12, 0.9)], 0.004, M('grey_plastic'), c)
    return c


vitals_stand('Vitals_Stand')


# =============================================================== seating, signs, wall items
def waiting_chair(name):
    c = T(name)
    rods(name + '_Legs', [((-0.22, -0.22, 0.0), (-0.22, -0.22, 0.45)), ((0.22, -0.22, 0.0), (0.22, -0.22, 0.45)),
                          ((-0.22, 0.2, 0.0), (-0.22, 0.24, 0.85)), ((0.22, 0.2, 0.0), (0.22, 0.24, 0.85)),
                          ((-0.24, -0.22, 0.65), (-0.24, 0.2, 0.65)), ((0.24, -0.22, 0.65), (0.24, 0.2, 0.65)),
                          ((-0.24, -0.22, 0.65), (-0.24, -0.22, 0.45)), ((0.24, -0.22, 0.65), (0.24, -0.22, 0.45))],
         0.011, M('chrome'), c)
    box(name + '_Seat', (0.5, 0.48, 0.07), (0, -0.01, 0.48), M('vinyl_teal'), c, bevel=0.025, segs=3)
    box(name + '_Back', (0.5, 0.06, 0.38), (0, 0.24, 0.72), M('vinyl_teal'), c, rot=(-0.12, 0, 0), bevel=0.025,
        segs=3)
    for sx in (-1, 1):
        box(name + f'_ArmPad_{sx}', (0.05, 0.4, 0.025), (sx * 0.245, -0.01, 0.665), M('black_plastic'), c,
            bevel=0.008)
    return c


waiting_chair('Waiting_Chair')


def wet_floor_sign(name):
    c = T(name)
    for sy in (-1, 1):
        a = sy * 13 * D2R
        p = box(name + f'_Panel_{sy}', (0.3, 0.012, 0.62), (0, sy * 0.075, 0.31), M('yellow'), c, rot=(a, 0, 0),
                bevel=0.006)
        rot = (PI / 2 - abs(a), 0, 0 if sy < 0 else PI)
        for nm, body, sz, z in (('T1', 'CAUTION', 0.055, 0.47), ('T2', 'WET FLOOR', 0.04, 0.33)):
            ys = sy * (0.075 - (z - 0.31) * math.tan(abs(a)) + 0.0105)
            text(name + f'_{nm}_{sy}', body, sz, (0, ys, z), rot, M('sign_text_dark'), c, extrude=0.001)
    cyl(name + '_Handle', 0.02, 0.18, (0, 0, 0.64), M('yellow'), c, rot=(0, PI / 2, 0), seg=12)
    return c


wet_floor_sign('Wet_Floor_Sign')


def noticeboard(name, w=1.3, h=0.9, seed=3):
    """Faces -Y, origin at the wall surface, centre of board."""
    c = T(name)
    r = random.Random(seed)
    box_minmax(name + '_Frame', (-w / 2 - 0.03, -0.03, -h / 2 - 0.03), (w / 2 + 0.03, 0, h / 2 + 0.03), M('wood'), c,
               bevel=0.008)
    box_minmax(name + '_Cork', (-w / 2, -0.034, -h / 2), (w / 2, -0.02, h / 2), M('cork'), c)
    papers = [M('paper_white')] * 4 + [M('paper_yellow'), M('paper_pink'), M('paper_blue'), M('paper_green')]
    placed = 0
    tries = 0
    used = []
    while placed < 11 and tries < 400:
        tries += 1
        pw, ph = r.choice([(0.21, 0.297), (0.297, 0.21), (0.148, 0.21), (0.1, 0.1), (0.21, 0.297)])
        x = r.uniform(-w / 2 + pw / 2 + 0.03, w / 2 - pw / 2 - 0.03)
        z = r.uniform(-h / 2 + ph / 2 + 0.03, h / 2 - ph / 2 - 0.11)     # stay below the header strip
        rect = (x - pw / 2 - 0.02, x + pw / 2 + 0.02, z - ph / 2 - 0.02, z + ph / 2 + 0.02)
        if any(rect[0] < o[1] and o[0] < rect[1] and rect[2] < o[3] and o[2] < rect[3] for o in used):
            continue     # overlapping sheets z-fight
        used.append(rect)
        box(name + f'_Paper_{placed}', (pw, 0.001, ph), (x, -0.037 - (placed % 2) * 0.002, z), r.choice(papers), c,
            rot=(0, r.uniform(-0.04, 0.04), 0))
        sphere(name + f'_Pin_{placed}', 0.006, (x, -0.046, z + ph / 2 - 0.02), r.choice(
            [M('red'), M('blue'), M('yellow'), M('green_tank')]), c, seg=10, rings=6)
        placed += 1
    box_minmax(name + '_Header', (-w / 2 + 0.05, -0.04, h / 2 - 0.09), (w / 2 - 0.05, -0.034, h / 2 - 0.02),
               M('sign_panel'), c)
    text(name + '_Title', 'STAFF NOTICES', 0.045, (0, -0.044, h / 2 - 0.055), (PI / 2, 0, 0), M('sign_text'), c)
    return c


noticeboard('Noticeboard')
noticeboard('Noticeboard_B', 1.0, 0.75, seed=9)


def sanitizer(name):
    c = T(name)   # faces -Y, origin on wall
    box_minmax(name + '_Body', (-0.06, -0.1, -0.13), (0.06, 0, 0.13), M('white_plastic'), c, bevel=0.015)
    box_minmax(name + '_Window', (-0.03, -0.104, -0.02), (0.03, -0.098, 0.06), M('glass_dark'), c)
    box_minmax(name + '_Push', (-0.045, -0.11, -0.12), (0.045, -0.085, -0.07), M('blue'), c, bevel=0.008)
    box_minmax(name + '_Drip', (-0.07, -0.12, -0.3), (0.07, 0, -0.29), M('grey_plastic'), c, bevel=0.004)
    return c


sanitizer('Sanitizer')


def extinguisher(name):
    c = T(name)   # faces -Y, origin on wall at floor level
    box_minmax(name + '_Bracket', (-0.05, -0.02, 0.6), (0.05, 0, 1.15), M('metal_dark'), c)
    cyl(name + '_Body', 0.075, 0.48, (0, -0.1, 0.62), M('red'), c, base=True, seg=24, bevel=0.01)
    sphere(name + '_Top', 0.075, (0, -0.1, 1.1), M('red'), c, scale=(1, 1, 0.4), seg=24)
    box(name + '_Valve', (0.03, 0.03, 0.06), (0, -0.1, 1.15), M('chrome'), c, bevel=0.004)
    box(name + '_Lever', (0.14, 0.02, 0.012), (0.04, -0.1, 1.19), M('black_plastic'), c, bevel=0.003)
    tube(name + '_Hose', [(0.02, -0.1, 1.15), (0.09, -0.16, 1.05), (0.09, -0.17, 0.8), (0.07, -0.17, 0.72)], 0.008,
         M('rubber'), c)
    box(name + '_Label', (0.08, 0.002, 0.14), (0, -0.176, 0.85), M('paper_white'), c)
    box_minmax(name + '_Sign', (-0.1, -0.006, 1.35), (0.1, 0, 1.6), M('red'), c)
    text(name + '_SignTxt', 'FIRE', 0.06, (0, -0.010, 1.47), (PI / 2, 0, 0), M('sign_text'), c)
    return c


extinguisher('Extinguisher')


def plant(name):
    c = T(name)
    r = random.Random(5)
    cyl(name + '_Pot', 0.2, 0.42, (0, 0, 0), M('pot'), c, r2=0.16, base=True, seg=28, bevel=0.01)
    cyl(name + '_Soil', 0.17, 0.02, (0, 0, 0.39), M('soil'), c, base=True, seg=24)
    stems = []
    for k in range(26):
        a = r.uniform(0, 2 * PI)
        tilt = r.uniform(0.2, 1.1)
        L = r.uniform(0.35, 0.75)
        base = Vector((r.uniform(-0.05, 0.05), r.uniform(-0.05, 0.05), 0.4))
        d = Vector((math.sin(tilt) * math.cos(a), math.sin(tilt) * math.sin(a), math.cos(tilt)))
        tip = base + d * L
        stems.append((tuple(base), tuple(base + d * L * 0.5), 0.004))
        q = d.to_track_quat('Z', 'Y').to_euler()
        sphere(name + f'_Leaf_{k}', 1.0, tuple(base + d * L * 0.72), M('leaf'), c, scale=(0.05, 0.008, L * 0.3),
               seg=10, rings=8, rot=(q.x, q.y, q.z + r.uniform(-0.4, 0.4)))
    rods(name + '_Stems', stems, 0.004, M('leaf'), c, seg=5)
    return c


plant('Plant')


def wall_clock(name):
    c = T(name)   # faces -Y
    cyl(name + '_Rim', 0.16, 0.04, (0, -0.02, 0), M('black_plastic'), c, rot=(PI / 2, 0, 0), seg=40, bevel=0.01)
    cyl(name + '_Face', 0.145, 0.002, (0, -0.041, 0), M('clock_face'), c, rot=(PI / 2, 0, 0), seg=40)
    ticks = []
    for k in range(12):
        a = 2 * PI * k / 12
        ticks.append(((0.125 * math.sin(a), -0.043, 0.125 * math.cos(a)),
                      (0.105 * math.sin(a), -0.043, 0.105 * math.cos(a)), 0.004 if k % 3 else 0.006))
    rods(name + '_Ticks', ticks, 0.004, M('black_plastic'), c, seg=4)
    rods(name + '_Hands', [((0, -0.045, 0), (0.06, -0.045, 0.04), 0.005), ((0, -0.046, 0), (-0.03, -0.046, 0.1), 0.0035),
                           ((0, -0.047, 0), (0.05, -0.047, -0.1), 0.0015)], 0.004, M('black_plastic'), c, seg=6)
    return c


wall_clock('Wall_Clock')


# =============================================================== patient room (corridor face at x=0)
def patient_room(name):
    c = T(name)
    hw = layout.OW / 2
    X1, YA, YB, Hh, t = 4.0, -0.8, 4.0, layout.H, layout.T
    box_minmax(name + '_Floor', (t, YA - t, -0.1), (X1 + t, YB + t, 0.0), M('floor'), c)   # corridor floor covers the threshold
    box_minmax(name + '_Ceiling', (t, YA, Hh), (X1, YB, Hh + 0.04), M('ceiling_plain'), c)
    box_minmax(name + '_Wall_Near', (t, YA - t, 0), (X1 + t, YA, Hh + 0.04), M('wall'), c)
    box_minmax(name + '_Wall_Head', (t, YB, 0), (X1 + t, YB + t, Hh + 0.04), M('wall_room'), c)
    wy0, wy1, wz0, wz1 = 0.9, 3.1, 0.8, 2.3
    for nm, mn, mx in (('Ext_Bot', (X1, YA, 0), (X1 + t, YB, wz0)), ('Ext_Top', (X1, YA, wz1), (X1 + t, YB, Hh + 0.04)),
                       ('Ext_A', (X1, YA, wz0), (X1 + t, wy0, wz1)), ('Ext_B', (X1, wy1, wz0), (X1 + t, YB, wz1))):
        box_minmax(name + '_Wall_' + nm, mn, mx, M('wall'), c)
    for nm, mn, mx in (('L', (X1, wy0, wz0), (X1 + 0.06, wy0 + 0.05, wz1)), ('R', (X1, wy1 - 0.05, wz0), (X1 + 0.06, wy1, wz1)),
                       ('B', (X1, wy0, wz0), (X1 + 0.06, wy1, wz0 + 0.05)), ('T', (X1, wy0, wz1 - 0.05), (X1 + 0.06, wy1, wz1)),
                       ('M', (X1, 1.97, wz0), (X1 + 0.06, 2.03, wz1))):
        box_minmax(name + '_WinFrame_' + nm, mn, mx, M('alu'), c, bevel=0.005)
    g = box_minmax(name + '_WinGlass', (X1 + 0.03, wy0, wz0), (X1 + 0.034, wy1, wz1), M('glass'), c)
    g.visible_shadow = False
    box_minmax(name + '_WinSill', (X1 - 0.08, wy0 - 0.05, wz0 - 0.03), (X1 + 0.01, wy1 + 0.05, wz0 + 0.005), M('counter_top'), c)
    sky = box_minmax(name + '_Outside', (X1 + 2.5, YA - 4, -6), (X1 + 2.6, YB + 4, 8), M('city_far'), c)
    box_minmax(name + '_Outside_Sky', (X1 + 6.5, YA - 8, -6), (X1 + 6.6, YB + 8, 14), M('sky'), c)
    # skirting around the room
    box_minmax(name + '_Skirt_Head', (t, YB - 0.012, 0), (X1, YB, 0.1), M('skirting'), c)
    box_minmax(name + '_Skirt_Ext', (X1 - 0.012, YA, 0), (X1, YB, 0.1), M('skirting'), c)
    # ceiling light (off) + curtain track
    box_minmax(name + '_CeilLight', (1.5, 0.9, Hh - 0.03), (2.7, 1.5, Hh), M('light_off'), c)
    track = [(0.75, 3.95, Hh - 0.03), (0.75, 1.3, Hh - 0.03), (3.45, 1.3, Hh - 0.03), (3.45, 3.95, Hh - 0.03)]
    tube(name + '_CurtainTrack', track, 0.012, M('alu'), c, fillet=0.2)
    # bunched curtain pulled back against the head wall (wavy sheet)
    cu = panel_grid(name + '_Curtain', 40, 12, (0.85, 2.2), M('curtain'), c, (0.75, 3.5, 1.65), (PI / 2, 0, PI / 2))
    for v in cu.data.vertices:
        u = v.co.x / 0.85 + 0.5
        v.co.z += 0.045 * math.sin(u * 2 * PI * 7) * (0.6 + 0.4 * u)
    cu.modifiers.new('Solid', 'SOLIDIFY').thickness = 0.004
    # headwall service panel
    box_minmax(name + '_Headwall', (1.0, YB - 0.06, 1.3), (3.2, YB, 1.68), M('beige_plastic'), c, bevel=0.01)
    for i, (x, m) in enumerate(((1.25, M('gas_green')), (1.4, M('gas_white')), (1.55, M('gas_yellow')))):
        cyl(name + f'_Gas_{i}', 0.03, 0.02, (x, YB - 0.07, 1.48), m, c, rot=(PI / 2, 0, 0), seg=18)
    for i in range(4):
        box_minmax(name + f'_Socket_{i}', (2.6 + i * 0.13, YB - 0.066, 1.42), (2.7 + i * 0.13, YB - 0.06, 1.52),
                   M('white_plastic'), c, bevel=0.004)
    box_minmax(name + '_ReadLight', (1.4, YB - 0.1, 1.95), (2.8, YB, 2.02), M('white_paint'), c, bevel=0.01)
    box_minmax(name + '_ReadLight_Glow', (1.45, YB - 0.1, 1.948), (2.75, YB - 0.02, 1.952), M('light_warm'), c)
    # bed (head against the head wall)
    lib.instance(name + '_Bed', T('Bed_Made'), c, (2.1, YB - 1.08, 0), (0, 0, 0))
    # patient monitor on wall arm
    box_minmax(name + '_MonArm_Base', (3.25, YB - 0.04, 1.85), (3.35, YB, 2.05), M('grey_plastic'), c)
    rods(name + '_MonArm', [((3.3, YB - 0.04, 1.95), (3.2, YB - 0.35, 1.95))], 0.02, M('grey_plastic'), c)
    box(name + '_Monitor', (0.36, 0.08, 0.28), (3.15, YB - 0.4, 1.95), M('grey_plastic'), c, rot=(0, 0, 0.5),
        bevel=0.015)
    box(name + '_Monitor_Screen', (0.3, 0.004, 0.21), (3.13, YB - 0.445, 1.96), M('screen_ecg'), c, rot=(0, 0, 0.5))
    # bedside cabinet
    box_minmax(name + '_Cabinet', (3.25, YB - 0.5, 0.05), (3.7, YB - 0.05, 0.8), M('wood'), c, bevel=0.012)
    box_minmax(name + '_Cabinet_Drawer', (3.27, YB - 0.505, 0.6), (3.68, YB - 0.49, 0.75), M('beige_plastic'), c,
               bevel=0.005)
    cyl(name + '_Cup', 0.035, 0.1, (3.4, YB - 0.3, 0.8), M('white_plastic'), c, base=True, seg=16)
    box_minmax(name + '_Tissues', (3.48, YB - 0.4, 0.8), (3.66, YB - 0.28, 0.88), M('paper_blue'), c, bevel=0.005)
    cyl(name + '_Jug', 0.05, 0.2, (3.55, YB - 0.15, 0.8), M('iv_bag'), c, base=True, seg=16).visible_shadow = False
    # overbed table
    box_minmax(name + '_Table_Base', (0.75, 2.0, 0.03), (1.0, 2.6, 0.06), M('metal_dark'), c, bevel=0.01)
    rods(name + '_Table_Post', [((0.85, 2.3, 0.06), (0.85, 2.3, 0.88))], 0.025, M('metal_dark'), c)
    box_minmax(name + '_Table_Top', (0.8, 2.05, 0.88), (2.0, 2.5, 0.91), M('beige_plastic'), c, bevel=0.01)
    box_minmax(name + '_Tray', (1.3, 2.12, 0.91), (1.7, 2.42, 0.93), M('grey_plastic'), c, bevel=0.006)
    lib.instance(name + '_IV', T('IV_Pole'), c, (0.85, YB - 0.55, 0), (0, 0, 0.6))
    lib.instance(name + '_Chair', T('Waiting_Chair'), c, (3.45, 1.5, 0), (0, 0, -PI * 0.75))
    lib.instance(name + '_Sanitizer', T('Sanitizer'), c, (0.45, YB, 1.35), (0, 0, 0))
    # room lights: warm reading light + cool dusk window light
    ld = bpy.data.lights.new(name + '_Light_Read', 'AREA')
    ld.shape = 'RECTANGLE'; ld.size = 1.3; ld.size_y = 0.25
    ld.energy = 35; ld.color = (1.0, 0.68, 0.42)
    lo = lib.new_obj(name + '_Light_Read', ld, c, (2.1, YB - 0.25, 1.94), (0, 0, 0))
    ld = bpy.data.lights.new(name + '_Light_Window', 'AREA')
    ld.shape = 'RECTANGLE'; ld.size = 2.1; ld.size_y = 1.4
    ld.energy = 55; ld.color = (0.45, 0.6, 1.0)
    lib.new_obj(name + '_Light_Window', ld, c, (X1 - 0.05, 2.0, 1.55), (0, PI / 2, 0))
    ld = bpy.data.lights.new(name + '_Light_Fill', 'AREA')
    ld.size = 1.2; ld.energy = 6; ld.color = (0.9, 0.8, 0.7)
    lib.new_obj(name + '_Light_Fill', ld, c, (2.0, 1.2, Hh - 0.05), (0, 0, 0))
    return c


patient_room('Patient_Room')

# exclude the template tree from the view layer (instances still render)
lc = bpy.context.view_layer.layer_collection.children.get('_Templates')
if lc:
    lc.exclude = True
print('templates ok', len(C_T.children))
