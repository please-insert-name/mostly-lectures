"""Automatic scene QA. Run headless after every build; the report feeds the Reviewer step.

   Blender -b hospital_corridor.blend --python scripts/qa_check.py -- [--stills] [--templates] [--flicker DIR]

  --stills      render start/middle/end frames (50 %) to previews/qa/ and check highlight clipping
  --templates   render a close-up of every _Templates prop to previews/qa/templates/
  --flicker DIR measure one-frame flicker spikes in a rendered PNG sequence (frame_####.png)

Writes previews/qa/qa_report.md and exits with code 1 if any check FAILs."""
import bpy, sys, os, re, math, glob, importlib
from collections import defaultdict
from mathutils import Vector, Matrix

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # project root = parent of scripts/
sys.path.insert(0, PROJ + '/scripts')
try:                     # optional per-project settings (FLICKER_PATTERN, QA_* overrides)
    import layout
    importlib.reload(layout)
except ImportError:
    layout = None

ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
QA_DIR = PROJ + '/previews/qa'
os.makedirs(QA_DIR, exist_ok=True)
SCENE = bpy.data.scenes.get('Scene') or bpy.context.scene

# Reviewed overlaps that are hidden or intentional (regex on "A <-> B")
ZF_ALLOW = [
    r'Ceiling_(Corridor|Station) <-> (Wall_|Station_Wall_|Ceiling_)',  # wall tops buried in the ceiling slab
    r'Window_Frame_\w <-> Window_Glass', r'WinFrame_\w <-> .*WinGlass',  # glass edges inside frames
    r'(Lower_Cabinet|Filing_Cabinet) <-> Station_Skirting',             # backs against the wall
    r'Keyboard_\d <-> Monitor_\d_Base',                                  # resting on the desk
    r'Foot_Panel <-> .*Footboard',                                       # panel mounted on the board
    r'(Window_Frame_\w+|WinFrame_\w) <-> .*(Window_Frame_|WinFrame_)',     # same-material frame members butting
    r'Blanket_Flap_-?1 <-> .*Blanket_Top',                               # same-material blanket pieces
]
COL_ALLOW = [r'Filing_Drawer_\d -> Filing_Cabinet', r'Whiteboard -> Whiteboard_Frame']
ZF_ALLOW += getattr(layout, 'QA_ZF_ALLOW', [])
COL_ALLOW += getattr(layout, 'QA_COL_ALLOW', [])
EXPECT = getattr(layout, 'QA_EXPECT', dict(resolution=(1920, 1080, 100), fps=24, frames=(1, 192)))

results = []        # (status, check, detail lines)


def report(status, check, lines=()):
    results.append((status, check, list(lines)))
    print(f'QA {status:4s} {check}' + ''.join(f'\n       {l}' for l in list(lines)[:12]))


def owner_name(inst, ob):
    return (inst.parent.name + '/' if inst.is_instance and inst.parent else '') + ob.name


def instance_meshes(dg):
    """Yield (owner, original_parent_or_object, world_matrix, mesh) for every visible mesh-like instance."""
    for inst in dg.object_instances:
        ob = inst.object
        if ob.type not in {'MESH', 'CURVE', 'FONT'} or not inst.show_self:
            continue
        try:
            me = ob.to_mesh()
        except RuntimeError:
            continue
        if me is None or not len(me.vertices):
            ob.to_mesh_clear()
            continue
        src = inst.parent.original if inst.is_instance and inst.parent else ob.original
        yield owner_name(inst, ob), src, inst.matrix_world.copy(), me
        ob.to_mesh_clear()


# ------------------------------------------------------------------ geometry: z-fighting
def _sat_overlap(p, q):
    """Convex 2D polygons p, q overlap (separating axis test)."""
    for poly in (p, q):
        n = len(poly)
        for i in range(n):
            ex, ey = poly[(i + 1) % n][0] - poly[i][0], poly[(i + 1) % n][1] - poly[i][1]
            ax = (-ey, ex)
            pa = [ax[0] * v[0] + ax[1] * v[1] for v in p]
            qa = [ax[0] * v[0] + ax[1] * v[1] for v in q]
            if max(pa) <= min(qa) + 1e-6 or max(qa) <= min(pa) + 1e-6:
                return False
    return True


def check_zfight(dg, gap=0.003, min_area=2e-4, min_overlap=1e-4):
    faces, wall_planes = [], set()
    wall_pat = re.compile(r'(^|/)(Wall_|EndWall_|Station_Wall_|Wall_Start|Patient_Room_Wall_)')
    for owner, src, mw, me in instance_meshes(dg):
        if any(k in owner for k in ('Haze_Volume', 'Sky', 'City', 'Outside', 'Ground')):
            continue
        if wall_pat.search(owner):        # remember wall surfaces: faces pressed against them are invisible
            nm_w = mw.to_3x3().inverted().transposed()
            for p in me.polygons:
                n = (nm_w @ p.normal).normalized()
                ax = max(range(3), key=lambda i: abs(n[i]))
                if abs(n[ax]) > 0.9995:
                    wall_planes.add((ax, 1 if n[ax] > 0 else -1, round((mw @ me.vertices[p.vertices[0]].co)[ax], 3)))
        nm = mw.to_3x3().inverted().transposed()
        for p in me.polygons:
            if p.area < min_area:
                continue
            n = (nm @ p.normal).normalized()
            ax = max(range(3), key=lambda i: abs(n[i]))
            if abs(n[ax]) < 0.9995:
                continue
            pts = [mw @ me.vertices[v].co for v in p.vertices]
            if ax == 2 and n[2] < 0 and abs(pts[0].z) < 0.002:
                continue      # downward faces resting on the floor are never visible
            o = [i for i in range(3) if i != ax]
            poly = [(q[o[0]], q[o[1]]) for q in pts]
            faces.append((owner, ax, 1 if n[ax] > 0 else -1, sum(q[ax] for q in pts) / len(pts), poly))
    faces = [f for f in faces if (f[1], -f[2], round(f[3], 3)) not in wall_planes]
    buckets = defaultdict(list)
    for i, f in enumerate(faces):
        buckets[(f[1], f[2], round(f[3] / gap))].append(i)
    hits = defaultdict(float)
    for (ax, sgn, k), idx in buckets.items():
        cand = idx + buckets.get((ax, sgn, k + 1), [])
        for a_i in idx:
            A = faces[a_i]
            ar = (min(v[0] for v in A[4]), max(v[0] for v in A[4]), min(v[1] for v in A[4]), max(v[1] for v in A[4]))
            for b_i in cand:
                if b_i <= a_i:
                    continue
                B = faces[b_i]
                an, bn = A[0].split('/')[-1], B[0].split('/')[-1]
                if A[0] == B[0] or an == bn or abs(A[3] - B[3]) > gap:
                    continue
                br = (min(v[0] for v in B[4]), max(v[0] for v in B[4]), min(v[1] for v in B[4]), max(v[1] for v in B[4]))
                ow, oh = min(ar[1], br[1]) - max(ar[0], br[0]), min(ar[3], br[3]) - max(ar[2], br[2])
                if ow * oh > min_overlap and ow > 0 and oh > 0 and _sat_overlap(A[4], B[4]):
                    pair = ' <-> '.join(sorted((A[0], B[0])))
                    hits[(pair, 'XYZ'[ax] + ('+' if sgn > 0 else '-'), round(A[3], 3))] += ow * oh
    bad = [(a, k) for k, a in hits.items() if not any(re.search(r, k[0]) for r in ZF_ALLOW)]
    bad.sort(key=lambda t: -t[0])
    lines = [f'{a:.4f} m²  {k[1]} @ {k[2]:+.3f}  {k[0]}' for a, k in bad]
    status = 'FAIL' if any(a > 0.005 for a, _ in bad) else ('WARN' if bad else 'PASS')
    report(status, f'Coplanar overlapping faces (z-fighting), gap ≤ {gap * 1000:.0f} mm: {len(bad)} pairs', lines)


# ------------------------------------------------------------------ geometry: collisions
def check_collisions(dg, min_pen=0.003):
    # name prefixes of fixed architecture/furniture and the collections holding movable props (override in layout.py)
    static_pre = tuple(getattr(layout, 'QA_STATIC_PREFIXES', (
        'Handrail_', 'Bumper_', 'Wall_', 'Rail_Bracket_', 'Panel_', 'Skirting_', 'Station_Wall_', 'Station_Front',
        'Station_Desk', 'Station_Ledge', 'Lower_Cabinet', 'Filing_Cabinet', 'Whiteboard_Frame', 'EndWall_')))
    prop_cols = set(getattr(layout, 'QA_PROP_COLLECTIONS', ('04_Corridor_Props', '03_Nurse_Station', '05_Signage')))
    statics, parts = [], []
    for owner, src, mw, me in instance_meshes(dg):
        vs = [mw @ v.co for v in me.vertices]
        mn = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
        mx = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
        cols = {c.name for c in src.users_collection}
        if '/' not in owner and owner.startswith(static_pre) and not (cols & prop_cols):
            statics.append((owner, mn, mx))
        elif cols & prop_cols:
            parts.append((owner, src.name, mn, mx))
    seen = {}
    for pname, src, a0, a1 in parts:
        for sname, b0, b1 in statics:
            if src == sname or pname.split('/')[-1] == sname:
                continue
            pen = min(min(a1[i], b1[i]) - max(a0[i], b0[i]) for i in range(3))
            if pen > min_pen:
                base = re.sub(r'(_[LR])?_?\d+$', '', sname)
                key = f'{src} -> {base}'
                seen[key] = max(seen.get(key, 0), pen)
    bad = {k: v for k, v in seen.items() if not any(re.search(r, k) for r in COL_ALLOW)}
    lines = [f'{v * 1000:5.0f} mm  {k}' for k, v in sorted(bad.items(), key=lambda kv: -kv[1])]
    report('FAIL' if bad else 'PASS', f'Props intersecting walls / trim / furniture: {len(bad)}', lines)


# ------------------------------------------------------------------ geometry: mirrored text, depth precision
def check_mirrored_text(dg):
    bad = [owner_name(i, i.object) for i in dg.object_instances
           if i.object.type == 'FONT' and i.matrix_world.determinant() < 0]
    report('FAIL' if bad else 'PASS', 'Text inside negatively scaled (mirrored) instances', bad)


def check_clip():
    cam = SCENE.camera
    cs = cam.data.clip_start
    ratio = cam.data.clip_end / cs
    st = 'PASS' if cs >= 0.1 and ratio <= 5000 else 'WARN'
    report(st, f'Camera depth precision: clip {cs:g}–{cam.data.clip_end:g} m (ratio {ratio:.0f}, keep ≤ 5000, start ≥ 0.1)')


# ------------------------------------------------------------------ materials / textures
def check_textures():
    lines, fail = [], False
    for img in bpy.data.images:
        if img.source in {'FILE', 'SEQUENCE'} and not img.packed_file:
            path = bpy.path.abspath(img.filepath)
            if os.path.abspath(path).startswith(PROJ + '/render/'):
                continue      # pipeline output (e.g. the EXR sequence the grade reads) is produced by the render
            if img.source == 'SEQUENCE':
                path = re.sub(r'\d+(?=\.\w+$)', '*', path)
                ok = bool(glob.glob(path))
            else:
                ok = os.path.exists(path)
            if not ok:
                lines.append(f'missing file: {img.name} ({img.filepath})')
                fail = True
    # image textures driven by UVs need meshes that actually have UVs
    uv_mats = set()
    for m in bpy.data.materials:
        if not m.node_tree:
            continue
        for n in m.node_tree.nodes:
            if n.type == 'TEX_IMAGE':
                l = n.inputs['Vector'].links
                src = l[0].from_node if l else None
                while src is not None and src.type == 'MAPPING':
                    src = src.inputs['Vector'].links[0].from_node if src.inputs['Vector'].links else None
                if src is None or (src.type == 'TEX_COORD' and l and 'UV' in [s.name for s in src.outputs if s.links]):
                    uv_mats.add(m.name)
    for o in bpy.data.objects:
        if o.type == 'MESH' and not o.data.uv_layers and any(s.material and s.material.name in uv_mats for s in o.material_slots):
            lines.append(f'UV-mapped image texture on mesh without UVs: {o.name}')
            fail = True
    report('FAIL' if fail else 'PASS', 'Textures: files present, UV-driven images only on UV-mapped meshes', lines)


# ------------------------------------------------------------------ lighting / render
def check_lighting():
    lines, status = [], 'PASS'
    w = SCENE.world
    world_vol = bool(w and w.node_tree and any(n.type == 'OUTPUT_WORLD' and n.inputs['Volume'].links for n in w.node_tree.nodes))
    suns = [o for o in SCENE.objects if o.type == 'LIGHT' and o.data.type == 'SUN']
    if world_vol and suns and SCENE.render.engine == 'BLENDER_EEVEE':
        lines.append('world volume + sun light: EEVEE extinguishes the sun completely, use a bounded volume object')
        status = 'FAIL'
    for o in SCENE.objects:
        for s in getattr(o, 'material_slots', []):
            m = s.material
            transparent = m and m.surface_render_method in {'DITHERED', 'BLENDED'} and m.node_tree and any(
                n.type == 'BSDF_PRINCIPLED' and n.inputs['Alpha'].default_value < 0.5 for n in m.node_tree.nodes)
            if transparent and o.visible_shadow:
                lines.append(f'transparent glass casts shadows (blocks light): {o.name}')
                status = 'FAIL' if status == 'FAIL' else 'WARN'
    n_lights = sum(1 for i in bpy.context.evaluated_depsgraph_get().object_instances
                   if i.object.type == 'LIGHT' and i.object.data.use_shadow)
    pool = int(SCENE.eevee.shadow_pool_size)
    if n_lights > 12 and pool < 1024:
        lines.append(f'{n_lights} shadowed lights but shadow pool only {pool} MB (raise to 1024)')
        status = 'FAIL'
    lines.append(f'{n_lights} shadow-casting lights, shadow pool {pool} MB')
    report(status, 'Lighting setup (world volume vs sun, glass shadows, shadow pool)', lines)


def check_render_settings():
    r, lines = SCENE.render, []
    exp = EXPECT
    got = dict(resolution=(r.resolution_x, r.resolution_y, r.resolution_percentage), fps=r.fps,
               frames=(SCENE.frame_start, SCENE.frame_end))
    for k in exp:
        if exp[k] != got[k]:
            lines.append(f'{k}: expected {exp[k]}, got {got[k]}')
    if not SCENE.camera or not (SCENE.camera.animation_data and SCENE.camera.animation_data.action):
        lines.append('camera missing or not animated')
    outs = {}
    for sc in bpy.data.scenes:
        d = os.path.dirname(bpy.path.abspath(sc.render.filepath))
        if d in outs:
            lines.append(f'scenes {outs[d]} and {sc.name} write to the same folder {d}')
        outs[d] = sc.name
    report('FAIL' if lines else 'PASS', 'Render settings (1920×1080, 24 fps, 1–192, animated camera, separate outputs)', lines)


def check_logs():
    lines = []
    for p in sorted(glob.glob(PROJ + '/render/*log*.txt')):
        txt = open(p, errors='ignore').read()
        for pat in ('Shadow buffer full', 'Traceback', 'Error:', 'not found in'):
            c = txt.count(pat)
            if c:
                lines.append(f'{os.path.basename(p)}: {c}× "{pat}"')
    report('WARN' if lines else 'PASS', 'Render logs free of warnings/errors', lines)


# ------------------------------------------------------------------ optional: stills, templates, flicker
def render_stills():
    lines, status = [], 'PASS'
    old = (SCENE.render.resolution_percentage, SCENE.eevee.taa_render_samples, SCENE.render.filepath)
    SCENE.render.resolution_percentage, SCENE.eevee.taa_render_samples = 50, 32
    for f in (SCENE.frame_start, (SCENE.frame_start + SCENE.frame_end) // 2, SCENE.frame_end):
        SCENE.frame_set(f)
        bpy.ops.render.render(scene=SCENE.name)
        path = f'{QA_DIR}/still_{f:04d}.png'
        bpy.data.images['Render Result'].save_render(path, scene=SCENE)
        img = bpy.data.images.load(path)
        px = img.pixels[:]
        lum = [0.2126 * px[i] + 0.7152 * px[i + 1] + 0.0722 * px[i + 2] for i in range(0, len(px), 4)]
        clip = sum(1 for v in lum if v >= 0.995) / len(lum) * 100
        crush = sum(1 for v in lum if v <= 0.005) / len(lum) * 100
        bpy.data.images.remove(img)
        lines.append(f'frame {f}: {clip:.2f}% clipped highlights, {crush:.2f}% crushed blacks -> {os.path.basename(path)}')
        if clip > 2.0 or crush > 5.0:
            status = 'WARN'
    SCENE.render.resolution_percentage, SCENE.eevee.taa_render_samples, SCENE.render.filepath = old
    report(status, 'Composition stills (start/mid/end) and exposure clipping', lines)


def render_templates():
    out = QA_DIR + '/templates'
    os.makedirs(out, exist_ok=True)
    sc = bpy.data.scenes.new('QA_Turntable')
    sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_x, sc.render.resolution_y = 800, 600
    sc.eevee.taa_render_samples = 16
    sc.view_settings.view_transform = 'AgX'
    sc.world = bpy.data.worlds.new('QA_World')
    sc.world.use_nodes = True
    sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.6
    cam = bpy.data.objects.new('QA_Cam', bpy.data.cameras.new('QA_Cam'))
    sc.collection.objects.link(cam)
    sc.camera = cam
    for i, (rot, e) in enumerate((((0.9, 0, 0.6), 4.0), ((1.1, 0, -2.4), 1.5))):
        l = bpy.data.objects.new(f'QA_Key{i}', bpy.data.lights.new(f'QA_Key{i}', 'SUN'))
        l.data.energy = e
        l.rotation_euler = rot
        sc.collection.objects.link(l)
    done = []
    for col in bpy.data.collections['_Templates'].children:
        if col.name == 'T_Patient_Room':
            continue
        inst = bpy.data.objects.new('QA_Inst', None)
        inst.instance_type, inst.instance_collection = 'COLLECTION', col
        sc.collection.objects.link(inst)
        pts = []
        for o in col.all_objects:
            if o.type in {'MESH', 'CURVE'}:
                m = Matrix.LocRotScale(o.location, o.rotation_euler, o.scale)
                pts += [m @ Vector(c) for c in o.bound_box]
        if not pts:
            sc.collection.objects.unlink(inst)
            continue
        mn = Vector([min(p[i] for p in pts) for i in range(3)])
        mx = Vector([max(p[i] for p in pts) for i in range(3)])
        c, rad = (mn + mx) / 2, max((mx - mn).length / 2, 0.15)
        d = Vector((0.55, 1.0, -0.5)).normalized()     # view direction: from front-left, above (props face -Y)
        cam.location = c - d * rad * 4.2
        cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        cam.data.lens = 50
        sc.render.filepath = f'{out}/{col.name}.png'
        bpy.ops.render.render(write_still=True, scene=sc.name)
        bpy.data.objects.remove(inst)
        done.append(col.name)
    for o in list(sc.collection.objects):
        bpy.data.objects.remove(o)
    bpy.data.scenes.remove(sc)
    report('INFO', f'Template close-ups for review: {len(done)} -> previews/qa/templates/', done)


def check_flicker(frame_dir, thresh=2.0, grid=(48, 27)):
    import numpy as np
    files = sorted(glob.glob(os.path.join(frame_dir, 'frame_*.png')))
    if len(files) < 3:
        report('FAIL', f'Flicker analysis: no frames in {frame_dir}')
        return
    gx, gy = grid
    frames = []
    for p in files:
        img = bpy.data.images.load(p)
        w, h = img.size
        a = np.empty(w * h * 4, np.float32)
        img.pixels.foreach_get(a)
        a = a.reshape(h, w, 4)[..., :3].mean(axis=2)
        frames.append(a[:h // gy * gy, :w // gx * gx].reshape(gy, h // gy, gx, w // gx).mean(axis=(1, 3)) * 255)
        bpy.data.images.remove(img)
    F = np.array(frames)
    prev, cur, nxt = F[:-2], F[1:-1], F[2:]
    spike = np.minimum(abs(cur - prev), abs(cur - nxt)) * (np.sign(cur - prev) == np.sign(cur - nxt))
    expected = set()
    for f in getattr(layout, 'FLICKER_PATTERN', {}):
        expected |= {f - 1, f, f + 1}
    lines, worst = [], 0.0
    for t in range(spike.shape[0]):
        f = t + 2
        m = float(spike[t].max())
        if m > thresh and f not in expected:
            worst = max(worst, m)
            y, x = np.unravel_index(spike[t].argmax(), spike[t].shape)
            lines.append(f'frame {f}: spike {m:.1f} at grid cell (col {x}, row {y}), {int((spike[t] > thresh).sum())} cells')
    status = 'FAIL' if worst > 8 else ('WARN' if worst > 4 else 'PASS')
    report(status, f'Temporal flicker in {os.path.relpath(frame_dir, PROJ)} (outside intentional panel flicker), '
                   f'worst {worst:.1f}', lines)


# ------------------------------------------------------------------ run
dg = bpy.context.evaluated_depsgraph_get()
check_zfight(dg)
check_collisions(dg)
check_mirrored_text(dg)
check_clip()
check_textures()
check_lighting()
check_render_settings()
check_logs()
if '--stills' in ARGS:
    render_stills()
if '--templates' in ARGS:
    render_templates()
if '--flicker' in ARGS:
    check_flicker(os.path.join(PROJ, ARGS[ARGS.index('--flicker') + 1]))

with open(QA_DIR + '/qa_report.md', 'w') as fh:
    fh.write(f'# QA report: {os.path.basename(bpy.data.filepath)}\n\n| Status | Check |\n|---|---|\n')
    for st, name, _ in results:
        fh.write(f'| {st} | {name} |\n')
    for st, name, lines in results:
        if lines:
            fh.write(f'\n## {st}: {name}\n' + ''.join(f'- {l}\n' for l in lines[:60]))
n_fail = sum(1 for r in results if r[0] == 'FAIL')
print(f'QA SUMMARY: {n_fail} FAIL, {sum(1 for r in results if r[0] == "WARN")} WARN, '
      f'{sum(1 for r in results if r[0] == "PASS")} PASS -> previews/qa/qa_report.md')
sys.exit(1 if n_fail else 0)
