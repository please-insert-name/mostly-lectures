"""Step 6 (v3): cinematic finishing pass as a compositing-only scene ('Grade_v3').

Reads the linear multilayer EXR sequence in render/exr/ (rendered once with compositing off), so the
grade can be changed and re-output in seconds per frame without re-rendering the 3D scene."""
import bpy, os

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # project root = parent of scripts/
EXR_FIRST = PROJ + '/render/exr/frame_0001.exr'
FRAMES = (1, 192)

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

scene = bpy.data.scenes.get('Grade_v3') or bpy.data.scenes.new('Grade_v3')
main = bpy.data.scenes.get('Scene') or next(s for s in bpy.data.scenes if s.name != 'Grade_v3')
r = scene.render
r.resolution_x, r.resolution_y, r.resolution_percentage = 1920, 1080, 100
r.fps, r.fps_base = 24, 1.0
scene.frame_start, scene.frame_end = FRAMES
r.use_compositing = True
scene.view_settings.view_transform = main.view_settings.view_transform
scene.view_settings.look = main.view_settings.look
scene.view_settings.exposure = main.view_settings.exposure
im = r.image_settings
im.media_type = 'IMAGE'
im.file_format = 'PNG'
im.color_mode = 'RGB'
im.color_depth = '8'
r.filepath = PROJ + '/render/frames_v3/frame_'
if scene.camera is None:      # render needs a camera even for compositing-only scenes
    cd = bpy.data.cameras.get('Grade_Dummy_Cam') or bpy.data.cameras.new('Grade_Dummy_Cam')
    cam = bpy.data.objects.get('Grade_Dummy_Cam') or bpy.data.objects.new('Grade_Dummy_Cam', cd)
    if cam.name not in scene.collection.objects:
        scene.collection.objects.link(cam)
    scene.camera = cam

old = bpy.data.node_groups.get('Grade_v3_Comp')
if old:
    bpy.data.node_groups.remove(old)
t = bpy.data.node_groups.new('Grade_v3_Comp', 'CompositorNodeTree')
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


# ---- source: linear EXR sequence
img = bpy.data.images.load(EXR_FIRST, check_existing=True)
img.source = 'SEQUENCE'
src = node('CompositorNodeImage')
src.image = img
src.frame_duration = FRAMES[1] - FRAMES[0] + 1
src.frame_start = FRAMES[0]
src.frame_offset = 0
src.use_auto_refresh = False   # live refresh of the EXR sequence crashed the UI session
base = next(o for o in src.outputs if o.name in ('Image', 'Combined') and o.enabled)

G = GRADE
ex = node('CompositorNodeExposure', Exposure=G['exposure'])
L.new(base, ex.inputs['Image'])
img_lin = ex.outputs['Image']

# ---- light effects (all computed from the clean image, added on top)
bloom = glare(img_lin, 'Bloom', G['bloom'])
hal = glare(img_lin, 'Bloom', G['halation'], Tint=G['halation']['tint'], Saturation=1.0)
stk = glare(img_lin, 'Streaks', G['streaks'], Streaks=G['streaks']['streaks'], Fade=G['streaks']['fade'],
            **{'Streaks Angle': G['streaks']['angle']})
sb = G['sunbeams']
win = mix(img_lin, ellipse_mask(img_lin, sb['pos'], sb['mask_size'], 30), 'MULTIPLY')
beams = glare(win, 'Sun Beams', sb, Saturation=0.0, Tint=sb['tint'], **{'Sun Position': sb['pos']})
acc = img_lin
for g in (bloom, hal, stk, beams):
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

# ---- animated film grain (multiplicative, so it scales with exposure like real grain)
coords = node('CompositorNodeImageCoordinates')
L.new(img_lin, coords.inputs['Image'])
vs = node('ShaderNodeVectorMath')
vs.operation = 'SCALE'
vs.inputs['Scale'].default_value = G['grain']['cell']
L.new(coords.outputs['Pixel'], vs.inputs[0])
tm = node('CompositorNodeSceneTime')
wn = node('ShaderNodeTexWhiteNoise')
wn.noise_dimensions = '4D'
L.new(vs.outputs['Vector'], wn.inputs['Vector'])
L.new(tm.outputs['Frame'], wn.inputs['W'])
g1 = node('ShaderNodeMath')
g1.operation = 'MULTIPLY_ADD'          # (v - 0.5) * amount + 1  ==  v * amount + (1 - amount / 2)
g1.inputs[1].default_value = G['grain']['amount']
g1.inputs[2].default_value = 1.0 - G['grain']['amount'] / 2
L.new(wn.outputs['Value'], g1.inputs[0])
final = mix(graded, g1.outputs[0], 'MULTIPLY')

out = node('NodeGroupOutput')
L.new(final, out.inputs[0])
print('grade scene ok', [o.name for o in src.outputs])
