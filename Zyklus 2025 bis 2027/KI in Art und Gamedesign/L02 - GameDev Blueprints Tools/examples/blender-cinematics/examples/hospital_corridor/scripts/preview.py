import bpy, time, sys
s = bpy.context.scene
F = int(globals().get('PREVIEW_FRAME', 1))
s.frame_set(F)
old = (s.render.resolution_percentage, s.eevee.taa_render_samples, s.render.filepath)
s.render.resolution_percentage = PCT if 'PCT' in globals() else 50
s.eevee.taa_render_samples = SAMPLES if 'SAMPLES' in globals() else 16
t = time.time()
bpy.ops.render.render(write_still=False)
img = bpy.data.images['Render Result']
path = bpy.path.abspath('//previews/') + (OUT if 'OUT' in globals() else 'preview.png')   # next to the saved .blend
img.save_render(path)
s.render.resolution_percentage, s.eevee.taa_render_samples, s.render.filepath = old
print('rendered', round(time.time() - t, 1), 's ->', path)
