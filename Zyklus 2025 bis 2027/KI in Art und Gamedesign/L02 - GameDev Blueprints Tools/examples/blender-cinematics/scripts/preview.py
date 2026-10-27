"""Low-res look-dev still of one hero shot via the socket (set SHOT, PCT, SAMPLES, OUT before it):
   SHOT = '01_Wide'   # shot name or camera name; default: the scene camera
Renders at the final still aspect (shots.STILL_RES) and writes previews/<OUT or preview_<shot>.png>."""
import bpy, time, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shots

s = bpy.data.scenes.get('Scene') or bpy.context.scene
want = globals().get('SHOT')
cam = next((c for c in shots.hero_cameras(s) if want in (c.name, shots.shot_name(c))), s.camera) if want else s.camera
r = s.render
old = (r.resolution_x, r.resolution_y, r.resolution_percentage, s.eevee.taa_render_samples, r.filepath, s.camera)
s.camera = cam
r.resolution_x, r.resolution_y = shots.STILL_RES
r.resolution_percentage = PCT if 'PCT' in globals() else 50
s.eevee.taa_render_samples = SAMPLES if 'SAMPLES' in globals() else 16
t = time.time()
bpy.ops.render.render(write_still=False, scene=s.name)
img = bpy.data.images['Render Result']
path = bpy.path.abspath('//previews/') + (OUT if 'OUT' in globals() else f'preview_{shots.shot_name(cam)}.png')   # next to the saved .blend
img.save_render(path, scene=s)
r.resolution_x, r.resolution_y, r.resolution_percentage, s.eevee.taa_render_samples, r.filepath, s.camera = old
print('rendered', cam.name, round(time.time() - t, 1), 's ->', path)
