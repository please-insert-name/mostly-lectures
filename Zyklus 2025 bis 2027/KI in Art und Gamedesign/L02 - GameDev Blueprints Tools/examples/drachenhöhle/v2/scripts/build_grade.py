"""Cinematic finishing pass for the hero stills, as a compositing-only scene ('Grade_Cinematic').

Reads one linear multilayer EXR per shot from render/exr/ (rendered once with compositing off, see
render_exr_setup.py), so the grade can be changed and re-output in seconds without re-rendering the 3D scene.
render_grade.py runs this script once per shot (setting SHOT) and writes render/stills_cinematic/<shot>.png.
Run on its own, it builds the grade for the first EXR it finds, for look-dev in the UI."""
import bpy, os, sys, glob, zlib

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # project root = parent of scripts/
sys.path.insert(0, PROJ + '/scripts')
try:
    import layout
except ImportError:
    layout = None

GRADE = dict(
    exposure=-0.08,
    bloom=dict(threshold=1.2, strength=0.22, size=0.6),
    halation=dict(threshold=1.6, strength=0.14, size=0.85, tint=(1.0, 0.32, 0.12, 1)),
    streaks=dict(threshold=7.0, strength=0.06, streaks=4, fade=0.88, angle=0.0),
    sunbeams=dict(pos=(0.5, 0.47), size=0.35, strength=0.5, threshold=1.0,
                  mask_size=(0.15, 0.11), tint=(1.0, 0.72, 0.45, 1)),
    dispersion=0.012,
    lift=(0.99, 1.0, 1.01, 1), gamma=(1.0, 1.0, 1.0, 1), gain=(1.05, 1.0, 0.94, 1),
    saturation=0.3,          # ~70% desaturation
    vignette=dict(size=(0.92, 0.82), blur=260, amount=0.5),
    grain=dict(amount=0.06, cell=0.6),
)
# Project look from layout.GRADE replaces these defaults (merged one level deep, like the per-shot overrides).
# Per-shot overrides from layout.SHOT_GRADE are merged on top of that. None switches an effect off.
# The sun-beam source must sit on the window in each frame (pos/mask_size in 0..1 frame coordinates):
#   SHOT_GRADE = {'02_Medium': dict(sunbeams=dict(pos=(0.71, 0.55)), exposure=0.05), '03_Detail': dict(sunbeams=None)}
SHOT_GRADE = dict(getattr(layout, 'SHOT_GRADE', {}))

SHOT = globals().get('SHOT')
if SHOT is None:
    first = sorted(glob.glob(PROJ + '/render/exr/*.exr'))
    SHOT = os.path.splitext(os.path.basename(first[0]))[0] if first else 'none'
EXR = f'{PROJ}/render/exr/{SHOT}.exr'

G = {k: (dict(v) if isinstance(v, dict) else v) for k, v in GRADE.items()}
for over in (getattr(layout, 'GRADE', {}), SHOT_GRADE.get(SHOT, {})):
    for k, v in over.items():
        G[k] = {**G[k], **v} if isinstance(v, dict) and isinstance(G.get(k), dict) else v

scene = bpy.data.scenes.get('Grade_Cinematic') or bpy.data.scenes.new('Grade_Cinematic')
main = bpy.data.scenes.get('Scene') or next(s for s in bpy.data.scenes if s.name != 'Grade_Cinematic')
r = scene.render
r.resolution_x, r.resolution_y, r.resolution_percentage = main.render.resolution_x, main.render.resolution_y, 100
scene.frame_start = scene.frame_end = 1
r.use_compositing = True
scene.view_settings.view_transform = main.view_settings.view_transform
scene.view_settings.look = main.view_settings.look
scene.view_settings.exposure = main.view_settings.exposure
im = r.image_settings
im.media_type = 'IMAGE'
im.file_format = 'PNG'
im.color_mode = 'RGB'
im.color_depth = '16'
r.filepath = f'{PROJ}/render/stills_cinematic/{SHOT}'
if scene.camera is None:      # render needs a camera even for compositing-only scenes
    cd = bpy.data.cameras.get('Grade_Dummy_Cam') or bpy.data.cameras.new('Grade_Dummy_Cam')
    cam = bpy.data.objects.get('Grade_Dummy_Cam') or bpy.data.objects.new('Grade_Dummy_Cam', cd)
    if cam.name not in scene.collection.objects:
        scene.collection.objects.link(cam)
    scene.camera = cam

old = bpy.data.node_groups.get('Grade_Cinematic_Comp')
if old:
    bpy.data.node_groups.remove(old)
t = bpy.data.node_groups.new('Grade_Cinematic_Comp', 'CompositorNodeTree')
t.interface.new_socket(name='Image', in_out='OUTPUT', socket_type='NodeSocketColor')
scene.compositing_node_group = t
N, L = t.nodes, t.links
X = [-2400]


def node(kind, **inputs):
    n = N.new(kind)
    n.location = (X[0], 0)
    X[0] += 220
    for k, v in inputs.items():
        n.inputs[k].default_value = v
    return n


def sock(n, ident, out=False):
    return next(s for s in (n.outputs if out else n.inputs) if s.identifier == ident)


def mix(a, b, blend, fac=1.0):
    m = node('ShaderNodeMix')
    m.data_type = 'RGBA'
    m.blend_type = blend
    sock(m, 'Factor_Float').default_value = fac
    L.new(a, sock(m, 'A_Color'))
    if isinstance(b, bpy.types.NodeSocket):
        L.new(b, sock(m, 'B_Color'))
    else:
        sock(m, 'B_Color').default_value = b
    return sock(m, 'Result_Color', True)


def glare(src, kind, g, **extra):
    n = node('CompositorNodeGlare')
    n.inputs['Type'].default_value = kind
    n.inputs['Quality'].default_value = 'High'
    n.inputs['Threshold'].default_value = g.get('threshold', 1.0)
    n.inputs['Strength'].default_value = g.get('strength', 1.0)
    if 'size' in g:
        n.inputs['Size'].default_value = g['size']
    for k, v in extra.items():
        n.inputs[k].default_value = v
    L.new(src, n.inputs['Image'])
    return n


def ellipse_mask(ref, pos, size, blur):
    zero = node('ShaderNodeMath', )
    zero.operation = 'MULTIPLY'
    zero.inputs[1].default_value = 0.0
    L.new(ref, zero.inputs[0])
    e = node('CompositorNodeEllipseMask')
    e.inputs['Position'].default_value = pos
    e.inputs['Size'].default_value = size
    L.new(zero.outputs[0], e.inputs['Mask'])
    b = node('CompositorNodeBlur')
    b.inputs['Size'].default_value = (blur, blur)
    L.new(e.outputs['Mask'], b.inputs['Image'])
    return b.outputs['Image']


# ---- source: the shot's linear EXR (a placeholder image until render_exr_setup.py has run)
if os.path.exists(EXR):
    img = bpy.data.images.load(EXR, check_existing=True)
    img.reload()                 # pick up a re-rendered EXR with the same name
else:
    print('grade scene: no EXR yet (run render_exr_setup.py):', EXR)
    img = bpy.data.images.get('Grade_Placeholder') or bpy.data.images.new('Grade_Placeholder', 16, 16, float_buffer=True)
src = node('CompositorNodeImage')
src.image = img
base = next(o for o in src.outputs if o.name in ('Image', 'Combined') and o.enabled)

ex = node('CompositorNodeExposure', Exposure=G['exposure'])
L.new(base, ex.inputs['Image'])
img_lin = ex.outputs['Image']

# ---- light effects (all computed from the clean image, added on top; None in the grade skips one)
fx = []
if G['bloom']:
    fx.append(glare(img_lin, 'Bloom', G['bloom']))
if G['halation']:
    fx.append(glare(img_lin, 'Bloom', G['halation'], Tint=G['halation']['tint'], Saturation=1.0))
if G['streaks']:
    fx.append(glare(img_lin, 'Streaks', G['streaks'], Streaks=G['streaks']['streaks'], Fade=G['streaks']['fade'],
                    **{'Streaks Angle': G['streaks']['angle']}))
sb = G['sunbeams']
if sb:
    win = mix(img_lin, ellipse_mask(img_lin, sb['pos'], sb['mask_size'], 30), 'MULTIPLY')
    fx.append(glare(win, 'Sun Beams', sb, Saturation=0.0, Tint=sb['tint'], **{'Sun Position': sb['pos']}))
acc = img_lin
for g in fx:
    acc = mix(acc, sock(g, 'Glare', True), 'ADD')

# ---- lens: chromatic dispersion
lens = node('CompositorNodeLensdist', Distortion=0.0, Dispersion=G['dispersion'], Fit=True)
L.new(acc, lens.inputs['Image'])

# ---- grade: teal shadows / warm highlights, gentle saturation lift
cb = node('CompositorNodeColorBalance')
cb.inputs['Type'].default_value = 'Lift/Gamma/Gain'
sock(cb, 'Color Lift').default_value = G['lift']
sock(cb, 'Color Gamma').default_value = G['gamma']
sock(cb, 'Color Gain').default_value = G['gain']
L.new(lens.outputs['Image'], cb.inputs['Image'])
hs = node('CompositorNodeHueSat', Saturation=G['saturation'])
L.new(cb.outputs['Image'], hs.inputs['Image'])
graded = hs.outputs['Image']

# ---- vignette
vg = G['vignette']
graded = mix(graded, ellipse_mask(img_lin, (0.5, 0.5), vg['size'], vg['blur']), 'MULTIPLY', vg['amount'])

# ---- film grain (multiplicative, so it scales with exposure like real grain); a fixed seed per shot
coords = node('CompositorNodeImageCoordinates')
L.new(img_lin, coords.inputs['Image'])
vs = node('ShaderNodeVectorMath')
vs.operation = 'SCALE'
vs.inputs['Scale'].default_value = G['grain']['cell']
L.new(coords.outputs['Pixel'], vs.inputs[0])
wn = node('ShaderNodeTexWhiteNoise')
wn.noise_dimensions = '4D'
wn.inputs['W'].default_value = zlib.crc32(SHOT.encode()) % 1000
L.new(vs.outputs['Vector'], wn.inputs['Vector'])
g1 = node('ShaderNodeMath')
g1.operation = 'MULTIPLY_ADD'          # (v - 0.5) * amount + 1  ==  v * amount + (1 - amount / 2)
g1.inputs[1].default_value = G['grain']['amount']
g1.inputs[2].default_value = 1.0 - G['grain']['amount'] / 2
L.new(wn.outputs['Value'], g1.inputs[0])
final = mix(graded, g1.outputs[0], 'MULTIPLY')

out = node('NodeGroupOutput')
L.new(final, out.inputs[0])
print('grade scene ok', SHOT, [o.name for o in src.outputs])
