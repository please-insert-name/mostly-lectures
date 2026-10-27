"""Debug: dragon silhouette sheet (front / side / top) with the cave hidden -> previews/dragon_sheet_<view>.png"""
import bpy
from mathutils import Vector
s = bpy.data.scenes['Scene']
HIDE = [o for o in s.objects if o.name.startswith(('Cave_', 'Haze', 'Beam_Haze', 'Sky', 'Dust', 'Vines', 'Ruins', 'Gate'))]
for o in HIDE:
    o.hide_render = True
r = s.render
old = (r.resolution_x, r.resolution_y, s.eevee.taa_render_samples, s.camera)
cd = bpy.data.cameras.new('TMP_Sheet'); cd.type, cd.ortho_scale = 'ORTHO', 18
cam = bpy.data.objects.new('TMP_Sheet', cd); s.collection.objects.link(cam)
c = Vector((1.5, 2.0, 3.5))
r.resolution_x, r.resolution_y, s.eevee.taa_render_samples = 900, 500, 8
s.camera = cam
for name, d in (('front', Vector((0, -1, 0))), ('side', Vector((1, 0, 0))), ('top', Vector((0, -0.001, 1)))):
    cam.location = c + d * 40
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    bpy.ops.render.render(scene=s.name)
    bpy.data.images['Render Result'].save_render(bpy.path.abspath(f'//previews/dragon_sheet_{name}.png'), scene=s)
for o in HIDE:
    o.hide_render = False
r.resolution_x, r.resolution_y, s.eevee.taa_render_samples, s.camera = old
bpy.data.objects.remove(cam)
print('sheet ok')
