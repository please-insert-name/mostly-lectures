"""Render the main scene as linear multilayer EXRs (compositing off) for the grading pass.
   Blender -b hospital_corridor.blend --python-exit-code 1 --python scripts/render_exr_setup.py
The render runs from inside this script, so a setup error can never fall through to a wrong render."""
import bpy

s = bpy.data.scenes.get('Scene') or bpy.context.scene
s.render.use_compositing = False
im = s.render.image_settings
im.media_type = 'MULTI_LAYER_IMAGE'     # Blender 5.x: this alone selects OPEN_EXR_MULTILAYER
im.color_depth = '16'
im.exr_codec = 'DWAA'
s.render.filepath = '//render/exr/frame_'
assert im.file_format == 'OPEN_EXR_MULTILAYER', im.file_format
print('EXR SETUP OK', im.media_type, im.file_format, im.color_depth, im.exr_codec)
bpy.ops.render.render(animation=True, scene=s.name)
