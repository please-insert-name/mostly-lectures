"""Hero shots: the cameras that produce the final cinematic stills.

A shot is a camera object named Hero_Cam_* (sorted by name), or the list layout.SHOTS when a project defines it.
The shot name used for files is the camera name without the 'Hero_Cam_' prefix, e.g. Hero_Cam_01_Wide -> 01_Wide.

    import shots
    shots.hero_camera('Hero_Cam_01_Wide', loc=(0, 0.6, 1.55), target=(0, 14, 1.2), lens=24, fstop=4.0)
    for cam in shots.hero_cameras(scene): ...
"""
import bpy, os, sys, importlib
from mathutils import Vector

PREFIX = 'Hero_Cam_'
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # project root = parent of scripts/
if PROJ + '/scripts' not in sys.path:
    sys.path.insert(0, PROJ + '/scripts')
try:                     # optional per-project settings (SHOTS, STILL_*, QA_* overrides)
    import layout
    importlib.reload(layout)
except ImportError:
    layout = None

# Final still format: 2.39:1 anamorphic widescreen. Override in layout.py (e.g. (1920, 1080) for 16:9, (3840, 1608) for 4K).
STILL_RES = tuple(getattr(layout, 'STILL_RES', (1920, 804)))
STILL_SAMPLES = int(getattr(layout, 'STILL_SAMPLES', 128))


def shot_name(cam):
    return cam.name[len(PREFIX):] if cam.name.startswith(PREFIX) else cam.name


def hero_cameras(scene=None):
    scene = scene or bpy.data.scenes.get('Scene') or bpy.context.scene
    names = getattr(layout, 'SHOTS', None)
    if names:
        return [bpy.data.objects[n] for n in names]
    return sorted((o for o in scene.objects if o.type == 'CAMERA' and o.name.startswith(PREFIX)), key=lambda o: o.name)


def hero_camera(name, loc, target, lens=35, fstop=2.8, focus=None, collection='07_Camera', sensor=36.0):
    """Create or update a hero camera aimed at `target`, focused on `focus` (point, default = target).
    Low f-stops (1.4–2.8) give the shallow depth of field that reads as 'cinematic'; 4–8 keeps wide shots sharp."""
    cd = bpy.data.cameras.get(name) or bpy.data.cameras.new(name)
    cam = bpy.data.objects.get(name) or bpy.data.objects.new(name, cd)
    col = bpy.data.collections.get(collection)
    if col is None:
        col = bpy.data.collections.new(collection)
        bpy.context.scene.collection.children.link(col)
    if cam.name not in col.objects:
        col.objects.link(cam)
    cam.location = loc
    d = Vector(target) - Vector(loc)
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    cd.lens, cd.sensor_width, cd.sensor_fit = lens, sensor, 'HORIZONTAL'
    cd.clip_start, cd.clip_end = 0.1, 200.0
    cd.dof.use_dof = True
    cd.dof.aperture_fstop = fstop
    cd.dof.focus_distance = (Vector(focus or target) - Vector(loc)).length
    return cam


def apply_still_settings(scene):
    """Final-still render settings: resolution, samples, no motion blur (a still has no shutter interval)."""
    r = scene.render
    r.resolution_x, r.resolution_y = STILL_RES
    r.resolution_percentage = 100
    r.use_motion_blur = False
    scene.eevee.taa_render_samples = STILL_SAMPLES
