"""Rebuild the scene headless and save it (no running UI / MCP socket needed):
   Blender -b scene.blend --python scripts/build_all_bg.py [-- build_a.py build_b.py ...]
Without arguments it runs the standard build steps that exist in this scripts folder, in order."""
import bpy, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT = ('build_arch.py', 'build_templates.py', 'build_props.py', 'build_lighting.py', 'build_comp.py', 'build_grade.py')
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
steps = args or [f for f in DEFAULT if os.path.exists(os.path.join(HERE, f))]
for f in steps:
    path = os.path.join(HERE, f)
    print('BUILD STEP', f)
    exec(compile(open(path).read(), path, 'exec'), {'__name__': '__main__', '__file__': path})
bpy.data.orphans_purge(do_recursive=True)
bpy.ops.file.pack_all()
bpy.ops.wm.save_mainfile()
print('BUILD_BG_OK', len(bpy.data.objects), 'objects')
