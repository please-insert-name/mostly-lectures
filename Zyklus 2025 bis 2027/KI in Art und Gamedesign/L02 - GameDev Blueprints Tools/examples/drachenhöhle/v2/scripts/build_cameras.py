"""Hero cameras for the four stills (static, DOF on). Shot names follow scenes.md.
Close-ups are placed relative to the scene (the dragon's head bone, a treasure instance, the mound surface), so they
stay framed when the layout or the pose changes."""
import bpy, os, sys, importlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shots, layout as L
importlib.reload(shots); importlib.reload(L)

dg = bpy.context.evaluated_depsgraph_get()
mound = BVHTree.FromObject(bpy.data.objects['Hoard_Mound'], dg)
arm = bpy.data.objects['DragonArmature']


def bone(name):
    return arm.matrix_world @ arm.pose.bones[name].head


def above_mound(p, clearance):
    """Lift p so it sits `clearance` above the mound surface (cameras must not end up inside the gold)."""
    hit = mound.ray_cast(Vector((p.x, p.y, 40)), Vector((0, 0, -1)))
    return Vector((p.x, p.y, max(p.z, (hit[0].z if hit[0] else 0) + clearance)))


dg_me = bpy.data.objects['DragonMesh'].evaluated_get(dg)
_mw = dg_me.matrix_world


def faces(slot):
    """World centres and mean normal of the dragon faces using material slot `slot` (2 = former eyes, 3 = teeth)."""
    ps = [p for p in dg_me.data.polygons if p.material_index == slot]
    return [_mw @ p.center for p in ps], [(_mw.to_3x3() @ p.normal).normalized() for p in ps]


eye_c, eye_n = faces(2)
EYE = min(zip(eye_c, eye_n), key=lambda cn: cn[1].y)          # the eye that faces -Y (towards the cameras)
eye, eye_dir = EYE[0], Vector((EYE[1].x, EYE[1].y, 0)).normalized()
teeth = faces(3)[0]
snout = sum(teeth, Vector()) / len(teeth)
snout_dir = Vector(((snout - eye).x, (snout - eye).y, 0)).normalized()
portrait = (eye_dir + snout_dir * 0.6).normalized()           # three-quarter direction, used for the face light
profile = (eye_dir - snout_dir * 0.15).normalized()           # side profile: eye towards camera, snout to the side
crown = bpy.data.objects['Hero_Crown'].location + Vector((0, 0, 0.25))   # centre of the crown
body = Vector(L.DRAGON_LOC) + Vector((0, 0, 3.0))
to_body = Vector(((body - crown).x, (body - crown).y, 0)).normalized()
to_eye = Vector(((eye - crown).x, (eye - crown).y, 0)).normalized()
dragon_bvh = BVHTree.FromObject(bpy.data.objects['DragonMesh'], dg)
near = dragon_bvh.find_nearest(crown)[0]
away = Vector(((crown - near).x, (crown - near).y, 0)).normalized()
from_head = Vector(((crown - eye).x, (crown - eye).y, 0)).normalized()   # camera in front of crown and head: head soft behind

CAM2 = above_mound(eye + profile * 9.0 + Vector((-0.6, 0, 0.7)), 0.4)
# along the portrait axis, closer in: the crown in front, the sleeping head soft above and behind it. The head lies
# bedded in coins, so it is only unobstructed from the front and from about eye height (lower or side views lose it)
CAM3 = crown + (CAM2 - crown).normalized() * 5.5
aim3 = ((crown - CAM3).normalized() * 0.7 + (eye - CAM3).normalized() * 0.3).normalized()

CAMS = [
    # name, location, look-at target, lens mm, f-stop, focus point (None = target)
    ('Hero_Cam_01_Wide', Vector((3.0, -19.5, 3.0)), Vector((-2.5, 6.0, 10.5)), 18, 8.0, Vector((0.5, 3.5, 4.0))),
    # in front of the sleeping face, slightly to the side and low, coins in the foreground
    ('Hero_Cam_02_DragonHead', CAM2, eye - (snout - eye) * 0.25 + Vector((0, 0, 0.45)), 40, 2.0, eye),
    # the crown in the sun, the dragon soft behind it
    ('Hero_Cam_03_TreasureDetail', CAM3, CAM3 + aim3, 40, 2.0, crown),
    # worm's-eye view from the foot of the mound up to the dragon and the light
    ('Hero_Cam_04_LowAngle', Vector((-3.0, -10.8, 0.28)), Vector((0.0, 3.0, 8.0)), 18, 4.0, Vector((0.0, 2.0, 4.0))),
]

for name, loc, target, lens, fstop, focus in CAMS:
    shots.hero_camera(name, tuple(loc), tuple(target), lens=lens, fstop=fstop, focus=tuple(focus) if focus else None)
# motivated face light for the portrait: sunlit gold bouncing up into the sleeping face (no shadow, local)
fl = bpy.data.objects.get('Face_Bounce')
if fl is None:
    fl = bpy.data.objects.new('Face_Bounce', bpy.data.lights.new('Face_Bounce', 'AREA'))
    bpy.data.collections['05_Lighting'].objects.link(fl)
fl.data.shape, fl.data.size, fl.data.energy = 'DISK', 2.5, 110
fl.data.color, fl.data.use_shadow = (1.0, 0.62, 0.3), False
fl.location = eye + portrait * 1.8 + Vector((0, 0, -1.3))
fl.rotation_euler = (eye - fl.location).to_track_quat('-Z', 'Y').to_euler()
# the crown is backlit by the sun: warm bounce from the sunlit coins in front of it opens up its face for shot 03
kl = bpy.data.objects.get('Crown_Bounce')
if kl is None:
    kl = bpy.data.objects.new('Crown_Bounce', bpy.data.lights.new('Crown_Bounce', 'AREA'))
    bpy.data.collections['05_Lighting'].objects.link(kl)
kl.data.shape, kl.data.size, kl.data.energy = 'DISK', 2.5, 220   # broad: metal only shows a light it can reflect
kl.data.color, kl.data.use_shadow = (1.0, 0.7, 0.35), False
kl.location = above_mound(crown + (CAM3 - crown).normalized() * 1.6, 0.25)
kl.rotation_euler = (crown - kl.location).to_track_quat('-Z', 'Y').to_euler()
print('eye', tuple(round(v, 2) for v in eye), 'snout', tuple(round(v, 2) for v in snout))

scene = bpy.data.scenes.get('Scene') or bpy.context.scene
scene.camera = bpy.data.objects[CAMS[0][0]]
shots.apply_still_settings(scene)
print('cameras ok', [(c[0], tuple(round(v, 1) for v in c[1])) for c in CAMS])
