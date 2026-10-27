"""Sleeping pose for the Poly Pizza 'Dragon Rigged' (na3ee1, CC-BY 3.0).

The rig faces -Y (L bones on +X) in its own frame (the root's rotation). All edits work in that frame about the bone's head, parents before children:
  ROT  (bone, axis, degrees)       +X pitches a forward-pointing chain down, +Z yaws -Y towards +X
  AIM  (bone, child, direction)    turns the segment bone.head -> child.head onto a world direction
The rig's bones are near zero-length, so segments are measured head to child head. Re-running resets the pose."""
import bpy
from math import radians
from mathutils import Matrix, Vector

ARM = 'DragonArmature'
JAW = globals().get('JAW', -20)     # closes the mouth (axis 'bx' = the bone's own X axis)
HEAD_DIR = globals().get('HEAD_DIR', (0.62, -0.78, 0.04))

ROT = [
    # neck curls down and round to the +X side, head comes to rest beside the forelimb
    ('Spine.005', 'X', 24), ('Spine.005', 'Z', 16),
    ('Spine.006', 'X', 22), ('Spine.006', 'Z', 20),
    ('Spine.007', 'X', 24), ('Spine.007', 'Z', 18),
    ('Spine.008', 'X', 10), ('Spine.008', 'Z', 22),
    ('Spine.009', 'X', 4), ('Spine.009', 'Z', 16),
    ('Jaw.001', 'bx', JAW),
    # tail wraps round the +X side towards the head
    ('Tail.001', 'X', -16),                       # tail points +Y: negative pitch lays it down
    ('Tail.002', 'Z', -30), ('Tail.002', 'X', -8), ('Tail.003', 'Z', -36), ('Tail.004', 'Z', -38),
    ('Tail.005', 'Z', -38), ('Tail.006', 'Z', -34), ('Tail.007', 'Z', -28),
    # hind legs tucked under the body
    ('Thigh.L', 'X', 55), ('Shin.L', 'X', -70),
    ('Thigh.R', 'X', 55), ('Shin.R', 'X', -70),
]

# the skull lies flat on the gold: top line of the head (SkullControl -> Head.005), snout to the +X side
HEAD = ('SkullControl', 'Head.005', HEAD_DIR)

# folded wings, written for the L side (+X); the R side is mirrored in X
WING = [
    ('Arm.{s}', 'Forearm.{s}', (0.42, 0.80, 0.30)),             # upper arm: elbow folded back, low along the flank
    ('Forearm.{s}', 'Finger1.{s}.001', (0.18, -0.88, -0.42)),   # forearm: lies forward on the ground like a cat's paw
    ('Finger1.{s}.001', 'Finger1.{s}.002', (0.16, 1.0, -0.22)),  # wing fingers fold back along the flank
    ('Finger1.{s}.002', 'Finger1.{s}.003', (0.12, 1.0, -0.20)),
    ('Finger2.{s}.001', 'Finger2.{s}.002', (0.20, 1.0, -0.12)),
    ('Finger2.{s}.002', 'Finger2.{s}.003', (0.14, 1.0, -0.12)),
    ('Finger3.{s}.001', 'Finger3.{s}.002', (0.24, 1.0, -0.02)),
    ('Finger3.{s}.002', 'Finger3.{s}.003', (0.18, 1.0, -0.04)),
    ('Finger4.{s}.001', 'Finger4.{s}.002', (0.28, 1.0, 0.08)),
    ('Finger4.{s}.002', 'Finger4.{s}.003', (0.22, 1.0, 0.04)),
]


def world_rot(arm, pb, m3):
    mw = arm.matrix_world
    h = mw @ pb.head
    r = Matrix.Translation(h) @ m3.to_4x4() @ Matrix.Translation(-h)
    pb.matrix = mw.inverted() @ r @ mw @ pb.matrix
    bpy.context.view_layer.update()


def frame(arm):
    """Rotation of the dragon's root: POSE axes/directions are in the dragon's own frame (it faces -Y)."""
    return arm.parent.matrix_world.to_3x3().normalized() if arm.parent else Matrix.Identity(3)


def rot(arm, name, axis, deg):
    pb = arm.pose.bones[name]
    if axis == 'bx':
        axis = (arm.matrix_world.to_3x3() @ pb.matrix.to_3x3() @ Vector((1, 0, 0))).normalized()
    else:
        axis = frame(arm) @ Vector({'X': (1, 0, 0), 'Y': (0, 1, 0), 'Z': (0, 0, 1)}[axis])
    world_rot(arm, pb, Matrix.Rotation(radians(deg), 3, axis))


def aim(arm, name, child, direction):
    mw = arm.matrix_world
    pb = arm.pose.bones[name]
    v = mw @ arm.pose.bones[child].head - mw @ pb.head
    world_rot(arm, pb, v.rotation_difference(frame(arm) @ Vector(direction)).to_matrix())


arm = bpy.data.objects[ARM]
if arm.animation_data:
    arm.animation_data.action = None
for pb in arm.pose.bones:
    pb.matrix_basis = Matrix.Identity(4)
bpy.context.view_layer.update()
for name, axis, deg in ROT:
    rot(arm, name, axis, deg)
aim(arm, *HEAD)
for side, sx in (('L', 1), ('R', -1)):
    for name, child, d in WING:
        aim(arm, name.format(s=side), child.format(s=side), (d[0] * sx, d[1], d[2]))
print('pose ok', len(ROT), 'rotations,', 2 * len(WING), 'aims')
