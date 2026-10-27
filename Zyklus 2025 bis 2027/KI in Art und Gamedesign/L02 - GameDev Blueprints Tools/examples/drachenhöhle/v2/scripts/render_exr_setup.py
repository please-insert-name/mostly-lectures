"""Render one linear multilayer EXR per hero shot (compositing off) for the grading pass.
   Blender -b scene.blend --python-exit-code 1 --python scripts/render_exr_setup.py [-- 01_Wide 03_Detail]
Without shot names it renders every hero shot (see shots.py) to render/exr/<shot>.exr.
The render runs from inside this script, so a setup error can never fall through to a wrong render."""
import bpy, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shots

s = bpy.data.scenes.get('Scene') or bpy.context.scene
s.render.use_compositing = False
shots.apply_still_settings(s)
im = s.render.image_settings
im.media_type = 'MULTI_LAYER_IMAGE'     # Blender 5.x: this alone selects OPEN_EXR_MULTILAYER
im.color_depth = '16'
im.exr_codec = 'DWAA'
assert im.file_format == 'OPEN_EXR_MULTILAYER', im.file_format

cams = shots.hero_cameras(s)
assert cams, 'no hero cameras (Hero_Cam_* or layout.SHOTS)'
want = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
if want:
    cams = [c for c in cams if shots.shot_name(c) in want]
    assert len(cams) == len(want), f'unknown shot in {want}'
print('EXR SETUP OK', im.media_type, im.file_format, im.color_depth, im.exr_codec,
      s.render.resolution_x, s.render.resolution_y, s.eevee.taa_render_samples, 'samples')
for cam in cams:
    s.camera = cam
    s.render.filepath = f'//render/exr/{shots.shot_name(cam)}'
    t = time.time()
    bpy.ops.render.render(write_still=True, scene=s.name)
    print(f'EXR {shots.shot_name(cam)}: {time.time() - t:.1f} s')
