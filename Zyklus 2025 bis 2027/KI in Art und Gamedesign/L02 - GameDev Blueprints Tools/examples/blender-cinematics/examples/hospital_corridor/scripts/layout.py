"""Single source of truth for the corridor layout (metres, +Y = down the corridor)."""

HW = 1.5          # half corridor width (corridor spans x -1.5 .. 1.5)
H = 2.8           # ceiling height
T = 0.15          # wall thickness
Y0, Y1 = -3.0, 34.0   # corridor start (behind camera) / end wall with window
OW, OH = 1.2, 2.2     # door opening width / height
FRAME = 0.06          # visible door frame width

# side, y centre, state, room number, vision-panel lit?
DOORS = [
    ('L', 4.5, 'closed', '402', False),
    ('L', 10.0, 'open', '404', True),
    ('L', 15.5, 'closed', '406', True),
    ('L', 21.0, 'open', '408', True),
    ('L', 26.5, 'closed', '410', False),
    ('R', 7.5, 'open', '403', True),
    ('R', 19.5, 'closed', '407', False),
    ('R', 24.5, 'ajar', '409', True),
    ('R', 29.5, 'closed', '411', True),
]

STATION = (12.5, 16.5)    # nurse station recess on the right wall (y range)
STATION_DEPTH = 3.0
STATION_OH = 2.5          # opening height (soffit above)

WINDOW = dict(x0=-1.3, x1=1.3, z0=0.75, z1=2.55, thick=0.3)

# Ceiling light panels: centre y, state
LIGHT_YS = [-1.8 + 3.0 * k for k in range(12)]
LIGHT_STATE = {1: 'off', 4: 'off', 6: 'off', 8: 'flicker', 9: 'off', 10: 'off', 11: 'off'}

# Intentional fluorescent stutter of panel 08: frame -> brightness factor (QA treats these frames as expected flicker)
FLICKER_PATTERN = {1: 1.0, 52: 1.0, 53: 0.15, 54: 0.8, 55: 0.05, 57: 1.0, 118: 1.0, 119: 0.3, 120: 1.0, 150: 1.0,
                   151: 0.1, 152: 0.1, 153: 0.9, 154: 0.2, 156: 1.0}

BULKHEADS = [18.0]


def side_sign(side):
    return 1.0 if side == 'R' else -1.0


def openings(side):
    """(y0, y1, top) openings cut through the corridor wall on one side."""
    out = []
    for s, y, state, num, lit in DOORS:
        if s == side and state in ('open', 'ajar'):
            out.append((y - OW / 2, y + OW / 2, OH))
    if side == 'R':
        out.append((STATION[0], STATION[1], STATION_OH))
    return sorted(out)


def frame_zones(side):
    """y ranges where wall trim (rails, panels) must stop: every door frame + station."""
    m = OW / 2 + FRAME + 0.01
    out = [(y - m, y + m) for s, y, *_ in DOORS if s == side]
    if side == 'R':
        out.append((STATION[0], STATION[1]))
    return sorted(out)


def subtract(a0, a1, holes):
    segs, cur = [], a0
    for h0, h1 in sorted(holes):
        if h1 <= cur or h0 >= a1:
            continue
        if h0 > cur:
            segs.append((cur, h0))
        cur = max(cur, h1)
    if cur < a1:
        segs.append((cur, a1))
    return segs
