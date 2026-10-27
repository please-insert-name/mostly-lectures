"""Full stills pipeline with QA gate (Windows, macOS, Linux). Run from the project root with the system Python:

   python scripts/render_stills.py scene.blend                     QA gate -> EXR per hero shot -> graded stills
   python scripts/render_stills.py scene.blend --shots 01_Wide     only these shots
   python scripts/render_stills.py scene.blend --grade-only        re-grade the existing EXRs (seconds, no 3D render)

Output: render/exr/<shot>.exr (linear) and render/stills_cinematic/<shot>.png (graded), QA report in previews/qa/.
Blender is found via the BLENDER environment variable, the PATH, or the default install folders."""
import argparse, glob, os, shutil, subprocess, sys, time

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = os.path.join(PROJ, 'scripts')


def find_blender():
    cands = [os.environ.get('BLENDER'), shutil.which('blender')]
    cands += sorted(glob.glob(r'C:\Program Files\Blender Foundation\Blender*\blender.exe'), reverse=True)
    cands += ['/Applications/Blender.app/Contents/MacOS/Blender']
    for c in cands:
        if c and os.path.exists(c):
            return c
    sys.exit('Blender not found: set the BLENDER environment variable to blender.exe')


def run(step, args, log):
    print(step, flush=True)
    t = time.time()
    with open(os.path.join(PROJ, log), 'w', encoding='utf-8') as fh:
        rc = subprocess.call(args, cwd=PROJ, stdout=fh, stderr=subprocess.STDOUT)
    lines = open(os.path.join(PROJ, log), encoding='utf-8', errors='ignore').read().splitlines()
    for l in lines:
        if l.startswith(('QA ', 'EXR', 'GRADED', 'Traceback', 'AssertionError', 'Error')):
            print('   ', l)
    if rc:
        sys.exit(f'{step} failed (exit {rc}), see {log}')
    print(f'    done in {time.time() - t:.0f} s')


ap = argparse.ArgumentParser()
ap.add_argument('blend')
ap.add_argument('--shots', nargs='*', default=[])
ap.add_argument('--grade-only', action='store_true')
a = ap.parse_args()
B, blend = find_blender(), os.path.abspath(a.blend)
for d in ('render/exr', 'render/stills_cinematic', 'previews/qa'):
    os.makedirs(os.path.join(PROJ, d), exist_ok=True)
sel = ['--', *a.shots] if a.shots else []

if not a.grade_only:
    run('1/3 QA gate', [B, '-b', blend, '--python', os.path.join(S, 'qa_check.py')], 'previews/qa/qa_gate_log.txt')
    run('2/3 linear EXRs', [B, '-b', blend, '--python-exit-code', '1', '--python', os.path.join(S, 'render_exr_setup.py'), *sel],
        'render/render_exr_log.txt')
run('3/3 graded stills', [B, '-b', blend, '--python-exit-code', '1', '--python', os.path.join(S, 'render_grade.py'), *sel],
    'render/render_grade_log.txt')

exrs = {os.path.splitext(os.path.basename(p))[0] for p in glob.glob(os.path.join(PROJ, 'render/exr/*.exr'))}
pngs = {os.path.splitext(os.path.basename(p))[0] for p in glob.glob(os.path.join(PROJ, 'render/stills_cinematic/*.png'))}
want = set(a.shots) or exrs
missing = sorted(want - pngs)
print(f'{len(want & pngs)} graded stills in render/stills_cinematic/' + (f', MISSING: {missing}' if missing else ''))
sys.exit(1 if missing else 0)
