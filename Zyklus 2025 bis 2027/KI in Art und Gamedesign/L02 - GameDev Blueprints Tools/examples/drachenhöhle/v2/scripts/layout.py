"""Single source of truth for the dragon cave (metres). +Y runs from the wide-shot camera towards the back wall."""

SEED = 7

# Cave shell: a displaced ellipsoid whose lower part is flattened into the floor
CAVE_CENTER = (0.0, 2.0, 5.0)
CAVE_RADII = (24.0, 26.0, 21.0)        # top of the dome at z = 26
CAVE_NOISE = dict(freq=0.11, amp=3.2, freq2=0.32, amp2=1.0)
FLOOR_Z = 0.0

# Hole in the ceiling (sun enters here), irregular radius
HOLE_XY = (-9.0, 9.0)
HOLE_R = 4.2

# Treasure mound under the dragon
HOARD_XY = (0.0, 3.0)
HOARD_R = 10.5
HOARD_H = 3.4
HEAD_PILE = (5.4, -2.9, 2.3, 1.82)   # x, y, radius, height: the pile the dragon's head rests on

CROWN_PREFER = (3.2, -4.3)        # on the sunny slope just below the sleeping head (shot 03 frames both)
CROWN_CLEARANCE = 1.5

# Dragon on top of the mound
DRAGON_LOC = (0.6, 3.6, 0.35)
DRAGON_SCALE = 1.9
DRAGON_ROT_Z = -25.0                  # degrees; the rig faces -Y at 0

# Sun: aimed from the hole at this point
SUN_TARGET = (3.6, -1.4, 3.3)         # the dragon's neck and head: the hotspot of the shot
SUN_COLOR = (1.0, 0.68, 0.40)
SUN_STRENGTH = 5.4

# Ruins of the old dwarven hall
COLUMNS = [  # x, y, height (None = full), state
    (-13.0, 14.0, None, 'intact'),
    (-5.0, 18.5, 7.0, 'broken'),
    (4.5, 19.0, None, 'intact'),
    (12.5, 15.0, 4.5, 'broken'),
    (16.0, 6.0, 2.2, 'stump'),
    (12.5, 2.5, 6.5, 'broken'),          # fills the right third of the wide and low-angle shots
]
COLUMN_R = 1.0
COLUMN_H = 13.0
FALLEN_COLUMN = dict(start=(10.0, 10.5), angle=-38.0, drums=6)
STAIRS = dict(x=-12.5, y=1.0, rot=-90.0, steps=9, width=6.0)   # climbs towards -X, gate at the wall

# Plants: where the sky light through the hole falls on the floor
PLANT_PATCH = dict(center=(-10.5, 10.5), radius=4.5)

# Shots (hero cameras are created in build_cameras.py)
STILL_RES = (1920, 804)
STILL_SAMPLES = 96


# Grade per shot: the sun-beam glare sits on the ceiling hole (0..1 frame coords, origin bottom left)
SHOT_GRADE = {
    '01_Wide': dict(sunbeams=dict(pos=(0.42, 0.92), mask_size=(0.13, 0.12))),
    '02_DragonHead': dict(sunbeams=None, exposure=-0.12, lift=(0.92, 0.945, 0.975, 1), saturation=1.0),   # through the beam haze: pull the veil down
    '03_TreasureDetail': dict(sunbeams=None, exposure=-0.45, bloom=dict(strength=0.14)),   # sunlit coins fill the frame
    '04_LowAngle': dict(sunbeams=dict(pos=(0.31, 0.94), mask_size=(0.16, 0.12))),
}

# QA
QA_SKIP = ('Hoard_Coins', 'Hoard_Spill', 'Hoard_Gems', 'Dust_Motes', 'Nostril_Smoke', 'Vines')
# the collision check compares object bounding boxes; ruins, boulders and plants are merged meshes spanning the cave,
# so every pair would 'collide'. Nothing here is a single wall-side prop, so the check is switched off.
QA_STATIC_PREFIXES = ('__none__',)
QA_PROP_COLLECTIONS = ()
QA_ZF_ALLOW = [r'Moss_Cushions <-> Ruins']   # undersides meeting below the floor (z -0.11), never visible

# Project look (overrides the skill's default grade): warm gold and red stay rich, teal shadows, slight desaturation
GRADE = dict(
    exposure=0.05,
    saturation=0.88,
    lift=(0.98, 1.0, 1.022, 1), gamma=(0.99, 1.0, 1.01, 1), gain=(1.06, 1.0, 0.86, 1),
    bloom=dict(threshold=1.0, strength=0.3, size=0.65),
    halation=dict(threshold=1.3, strength=0.16, size=0.85, tint=(1.0, 0.52, 0.16, 1)),
    vignette=dict(size=(0.95, 0.85), blur=260, amount=0.45),
    grain=dict(amount=0.045, cell=0.6),
)
