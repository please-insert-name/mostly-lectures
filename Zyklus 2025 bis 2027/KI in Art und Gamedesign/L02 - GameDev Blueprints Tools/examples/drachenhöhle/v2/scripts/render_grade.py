"""Output the cinematic grade for every shot that has an EXR: render/exr/<shot>.exr -> render/stills_cinematic/<shot>.png
   Blender -b scene.blend --python-exit-code 1 --python scripts/render_grade.py [-- 01_Wide 03_Detail]
Rebuilds the Grade_Cinematic node tree per shot (GRADE + layout.SHOT_GRADE), so re-grading takes seconds."""
import bpy, os, sys, glob, time

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
GRADE_SCRIPT = os.path.join(HERE, 'build_grade.py')

want = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
names = [os.path.splitext(os.path.basename(p))[0] for p in sorted(glob.glob(PROJ + '/render/exr/*.exr'))]
if want:
    missing = set(want) - set(names)
    assert not missing, f'no EXR for {sorted(missing)}'
    names = want
assert names, 'no EXRs in render/exr/ (run render_exr_setup.py first)'
os.makedirs(PROJ + '/render/stills_cinematic', exist_ok=True)
for shot in names:
    t = time.time()
    exec(compile(open(GRADE_SCRIPT, encoding='utf-8').read(), GRADE_SCRIPT, 'exec'),
         {'__name__': '__main__', '__file__': GRADE_SCRIPT, 'SHOT': shot})
    bpy.ops.render.render(write_still=True, scene='Grade_Cinematic')
    print(f'GRADED {shot}: {time.time() - t:.1f} s -> render/stills_cinematic/{shot}.png')
