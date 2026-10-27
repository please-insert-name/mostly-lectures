"""Debug: orthographic top view of the hoard area (cave shell, haze hidden) with the hero cameras marked
-> previews/topmap.png. Restores everything afterwards."""
import bpy
from mathutils import Vector

s = bpy.data.scenes.get('Scene') or bpy.context.scene
HIDE = ('Cave_Shell', 'Cave_Spikes', 'Haze_Volume', 'Sky_Plane', 'Dust_Motes', 'Vines', 'Nostril_Smoke')
old_cam, r = s.camera, s.render
old = (r.resolution_x, r.resolution_y, r.resolution_percentage, s.eevee.taa_render_samples)
cd = bpy.data.cameras.new('TMP_Top')
cd.type, cd.ortho_scale = 'ORTHO', 30.0
cam = bpy.data.objects.new('TMP_Top', cd)
s.collection.objects.link(cam)
cam.location = (0.5, 0.5, 40)
sun = bpy.data.objects.new('TMP_Sun', bpy.data.lights.new('TMP_Sun', 'SUN'))
sun.data.energy = 3
s.collection.objects.link(sun)
marks = []
for c in [o for o in s.objects if o.name.startswith('Hero_Cam_')]:
    m = bpy.data.objects.new('TMP_Mark_' + c.name, None)
    m.empty_display_type = 'CONE'
    s.collection.objects.link(m)
    marks.append(m)
for n in HIDE:
    bpy.data.objects[n].hide_render = True
s.camera = cam
r.resolution_x, r.resolution_y, r.resolution_percentage, s.eevee.taa_render_samples = 900, 900, 100, 8
bpy.ops.render.render(scene=s.name)
bpy.data.images['Render Result'].save_render(bpy.path.abspath('//previews/topmap.png'), scene=s)
for n in HIDE:
    bpy.data.objects[n].hide_render = False
s.camera = old_cam
r.resolution_x, r.resolution_y, r.resolution_percentage, s.eevee.taa_render_samples = old
for o in [cam, sun] + marks:
    bpy.data.objects.remove(o)
print('topmap: 30 m square centred on (0.5, 0.5); +X right, +Y up')
for c in [o for o in s.objects if o.name.startswith('Hero_Cam_')]:
    d = c.matrix_world.to_3x3() @ Vector((0, 0, -1))
    print(c.name, 'at', tuple(round(v, 1) for v in c.location), 'looking', tuple(round(v, 2) for v in d))
