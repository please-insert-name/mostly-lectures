"""Step 4: lights, haze, camera push-in and render settings (EEVEE, 1920x1080, 24 fps)."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # __file__ is injected by bl_client.py / build_all_bg.py
import bpy
import lib, layout
from lib import get_coll, M, D2R, PI
from layout import *
from mathutils import Vector

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # project root = parent of scripts/
scene = bpy.context.scene
C_LIGHT = get_coll('06_Lighting')
C_CAM = get_coll('07_Camera')
for c in (C_LIGHT, C_CAM):
    for o in list(c.objects):
        bpy.data.objects.remove(o, do_unlink=True)

FSTART, FEND = 1, 192


def area(name, size, size_y, energy, color, loc, rot=(0, 0, 0), spread=180):
    ld = bpy.data.lights.new(name, 'AREA')
    ld.shape = 'RECTANGLE'
    ld.size, ld.size_y = size, size_y
    ld.energy = energy
    ld.color = color
    ld.spread = spread * D2R
    return lib.new_obj(name, ld, C_LIGHT, loc, rot)


# ---------------------------------------------------------------- fluorescent ceiling panels
COOL = (0.86, 0.93, 1.0)
flicker_light = None
for k, yc in enumerate(LIGHT_YS):
    state = LIGHT_STATE.get(k, 'on')
    if state == 'off':
        continue
    o = area(f'Ceiling_Light_{k:02d}', 0.52, 1.12, 45.0, COOL, (0, yc, H - 0.04))
    if state == 'flicker':
        flicker_light = o

# flicker: mostly steady with a couple of brief stutters (light + emissive diffuser stay in sync)
mat = M('light_flicker')
mult = [n for n in mat.node_tree.nodes if n.type == 'MATH' and n.operation == 'MULTIPLY'
        and abs(n.inputs[1].default_value - 9.0) < 1e-4][0]
for f, v in FLICKER_PATTERN.items():
    flicker_light.data.energy = 45.0 * v
    flicker_light.data.keyframe_insert('energy', frame=f)
    mult.inputs[1].default_value = 9.0 * v
    mult.inputs[1].keyframe_insert('default_value', frame=f)


def set_constant(id_data):
    ad = id_data.animation_data
    if not ad or not ad.action:
        return
    try:
        curves = ad.action.fcurves
    except AttributeError:
        curves = [fc for layer in ad.action.layers for strip in layer.strips
                  for bag in strip.channelbags for fc in bag.fcurves]
    for fc in curves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'CONSTANT'


set_constant(flicker_light.data)
set_constant(mat.node_tree)

# ---------------------------------------------------------------- golden-hour sun through the end window
sd = bpy.data.lights.new('Sun_Golden_Hour', 'SUN')
sd.energy = 14.0
sd.color = (1.0, 0.48, 0.20)
sd.angle = 0.6 * D2R
sun = lib.new_obj('Sun_Golden_Hour', sd, C_LIGHT)
d = Vector((-0.10, -1.0, -0.125)).normalized()
sun.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
sun.location = (0, 40, 6)
# soft sky fill entering through the window
area('Window_Skyfill', 2.5, 1.7, 70.0, (1.0, 0.58, 0.34), (0, Y1 - 0.12, 1.65), (-PI / 2, 0, 0))
# faint cool bounce from the corridor start (keeps the foreground from going black)
area('Bounce_Start', 2.6, 2.0, 25.0, (0.75, 0.85, 1.0), (0, Y0 + 0.2, 1.4), (-PI / 2, 0, PI))

# ---------------------------------------------------------------- world: dusk + volumetric haze
world = bpy.data.worlds.get('Hospital_World') or bpy.data.worlds.new('Hospital_World')
scene.world = world
try:
    world.use_nodes = True
except Exception:
    pass
nt = world.node_tree
nt.nodes.clear()
out = nt.nodes.new('ShaderNodeOutputWorld')
bg = nt.nodes.new('ShaderNodeBackground')
bg.inputs['Color'].default_value = (0.015, 0.018, 0.03, 1)
bg.inputs['Strength'].default_value = 1.0
nt.links.new(bg.outputs[0], out.inputs['Surface'])
# NOTE: a world volume extinguishes sun lights in EEVEE, so the haze is a bounded volume
# that only fills the interior (corridor + nurse station).
hm = bpy.data.materials.get('Haze_Volume') or bpy.data.materials.new('Haze_Volume')
try:
    hm.use_nodes = True
except Exception:
    pass
hn = hm.node_tree
hn.nodes.clear()
ho = hn.nodes.new('ShaderNodeOutputMaterial')
hv = hn.nodes.new('ShaderNodeVolumePrincipled')
hv.inputs['Density'].default_value = 0.022
hv.inputs['Anisotropy'].default_value = 0.6
hv.inputs['Color'].default_value = (0.96, 0.96, 1.0, 1)
hn.links.new(hv.outputs[0], ho.inputs['Volume'])
haze = lib.box_minmax('Haze_Volume', (-HW, Y0, 0.0), (HW + STATION_DEPTH, Y1, H), hm, C_LIGHT)
haze.visible_shadow = False
haze.display_type = 'BOUNDS'

# ---------------------------------------------------------------- camera with slow push-in
cd = bpy.data.cameras.new('Cinematic_Camera')
cd.lens = 30
cd.sensor_width = 36
cd.clip_start = 0.1      # doubles depth precision in the distance (less z-fighting far away)
cd.clip_end = 250
cam = lib.new_obj('Cinematic_Camera', cd, C_CAM, (0, 0.6, 1.55), (90 * D2R, 0, 0))
focus = lib.empty('Camera_Focus_Target', C_CAM, (0, 14.5, 1.1))
cd.dof.use_dof = True
cd.dof.focus_object = focus
cd.dof.aperture_fstop = 2.2
cd.dof.aperture_blades = 7
scene.camera = cam

P0, P1 = Vector((0.0, 0.6, 1.56)), Vector((0.02, 4.4, 1.50))
R0, R1 = Vector((89.6 * D2R, 0, 0)), Vector((89.3 * D2R, 0, 0.15 * D2R))
for f, p, r in ((FSTART, P0, R0), (FEND, P1, R1)):
    cam.location = p
    cam.rotation_euler = r
    cam.keyframe_insert('location', frame=f)
    cam.keyframe_insert('rotation_euler', frame=f)


def soften_ease(obj, start_slope=0.55):
    """Bezier handles that start/end the move at ~55% of average speed (gentle, not a hard S-curve)."""
    ad = obj.animation_data
    try:
        curves = list(ad.action.fcurves)
    except AttributeError:
        curves = [fc for layer in ad.action.layers for strip in layer.strips
                  for bag in strip.channelbags for fc in bag.fcurves]
    for fc in curves:
        k0, k1 = fc.keyframe_points[0], fc.keyframe_points[-1]
        dx = k1.co.x - k0.co.x
        avg = (k1.co.y - k0.co.y) / dx
        hl = dx / 3
        for kp in (k0, k1):
            kp.interpolation = 'BEZIER'
            kp.handle_left_type = kp.handle_right_type = 'FREE'
        k0.handle_right = (k0.co.x + hl, k0.co.y + avg * start_slope * hl)
        k0.handle_left = (k0.co.x - hl, k0.co.y - avg * start_slope * hl)
        k1.handle_left = (k1.co.x - hl, k1.co.y - avg * start_slope * hl)
        k1.handle_right = (k1.co.x + hl, k1.co.y + avg * start_slope * hl)


soften_ease(cam)

# ---------------------------------------------------------------- render settings
scene.frame_start, scene.frame_end = FSTART, FEND
scene.render.fps = 24
scene.render.fps_base = 1.0
scene.render.resolution_x, scene.render.resolution_y = 1920, 1080
scene.render.resolution_percentage = 100
scene.render.engine = 'BLENDER_EEVEE'
ee = scene.eevee
ee.taa_render_samples = 64
ee.use_raytracing = True
ee.ray_tracing_method = 'SCREEN'
rto = ee.ray_tracing_options
rto.resolution_scale = '1'
rto.trace_max_roughness = 0.6
rto.use_denoise = True
ee.use_fast_gi = True
ee.fast_gi_method = 'GLOBAL_ILLUMINATION'
ee.fast_gi_resolution = '2'
ee.fast_gi_distance = 4.0
ee.fast_gi_ray_count = 2
ee.fast_gi_step_count = 8
ee.use_shadows = True
ee.shadow_ray_count = 2
ee.shadow_step_count = 10
ee.shadow_resolution_scale = 1.0
ee.shadow_pool_size = '1024'   # avoids 'shadow buffer full' with many shadowed lights
ee.use_volumetric_shadows = True
ee.volumetric_start = 0.1
ee.volumetric_end = 70.0
ee.volumetric_tile_size = '4'
ee.volumetric_samples = 96
ee.volumetric_shadow_samples = 24
ee.volumetric_light_clamp = 0.0
ee.use_overscan = True
ee.overscan_size = 0.04
ee.clamp_surface_indirect = 10.0
scene.render.use_motion_blur = True
scene.render.motion_blur_shutter = 0.5
scene.render.film_transparent = False
scene.render.filter_size = 1.5

vs = scene.view_settings
vs.view_transform = 'AgX'
for look in ('AgX - Medium High Contrast', 'Medium High Contrast', 'AgX - Punchy'):
    try:
        vs.look = look
        break
    except TypeError:
        continue
vs.exposure = -0.25
vs.gamma = 1.0

im = scene.render.image_settings
im.media_type = 'IMAGE'
im.file_format = 'PNG'
im.color_mode = 'RGB'
im.color_depth = '8'
im.compression = 15
scene.render.filepath = PROJ + '/render/frames/frame_'
scene.render.use_file_extension = True
scene.frame_set(FSTART)
print('lighting ok', vs.look, len(C_LIGHT.objects))
