"""Shared helpers for the dragon cave: collections, faceted meshes with per-face colour variation, materials.

Low-poly look: every mesh is flat shaded; each face carries a 'facevar' colour attribute (0..1 around 0.5) that the
materials use to vary brightness/hue per facet, so large faceted surfaces never look flat-filled."""
import bpy, bmesh, random
from mathutils import Vector

FV = 'facevar'


def coll(name, parent=None, hide=False):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    p = parent or bpy.context.scene.collection
    if c.name not in p.children:
        p.children.link(c)
    return c


def clear(col):
    for o in list(col.all_objects):
        bpy.data.objects.remove(o)


def bm_to_obj(bm, name, col, mats, var=0.5, rng=None, loc=(0, 0, 0)):
    """Finish a bmesh as a flat-shaded object with per-face variation (var = spread of 'facevar')."""
    rng = rng or random.Random(hash(name) & 0xffff)
    lay = bm.loops.layers.color.get(FV) or bm.loops.layers.color.new(FV)
    for f in bm.faces:
        f.smooth = False
        v = 0.5 + (rng.random() - 0.5) * var
        c = (v, rng.random(), 0.0, 1.0)            # R: brightness variation, G: free random (hue/moss)
        for l in f.loops:
            l[lay] = c
    me = bpy.data.meshes.get(name)
    if me:
        bpy.data.meshes.remove(me)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    col.objects.link(ob)
    return ob


# ------------------------------------------------------------------ materials
def _mat(name):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    return m, nt


def _bsdf(nt, out_loc=(400, 0)):
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    out.location = out_loc
    b = nt.nodes.new('ShaderNodeBsdfPrincipled')
    nt.links.new(b.outputs[0], out.inputs['Surface'])
    return b


def _facevar_color(nt, c_dark, c_light, c_alt=None, alt_amount=0.0):
    """Colour from the facevar attribute: R blends dark->light, G optionally mixes towards c_alt."""
    a = nt.nodes.new('ShaderNodeVertexColor')
    a.layer_name = FV
    sep = nt.nodes.new('ShaderNodeSeparateColor')
    nt.links.new(a.outputs['Color'], sep.inputs[0])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (*c_dark, 1)
    ramp.color_ramp.elements[1].color = (*c_light, 1)
    nt.links.new(sep.outputs[0], ramp.inputs[0])
    col = ramp.outputs[0]
    if c_alt is not None:
        g = nt.nodes.new('ShaderNodeMath')
        g.operation = 'GREATER_THAN'
        g.inputs[1].default_value = 1.0 - alt_amount
        nt.links.new(sep.outputs[1], g.inputs[0])
        mx = nt.nodes.new('ShaderNodeMix')
        mx.data_type = 'RGBA'
        nt.links.new(g.outputs[0], mx.inputs['Factor'])
        nt.links.new(col, mx.inputs[6])
        mx.inputs[7].default_value = (*c_alt, 1)
        col = mx.outputs[2]
    return col


def mat_facet(name, c_dark, c_light, rough=0.8, metal=0.0, c_alt=None, alt_amount=0.0, spec=0.5):
    m, nt = _mat(name)
    b = _bsdf(nt)
    nt.links.new(_facevar_color(nt, c_dark, c_light, c_alt, alt_amount), b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    b.inputs['Specular IOR Level'].default_value = spec
    return m


def mat_simple(name, color, rough=0.5, metal=0.0, emit=None, emit_strength=0.0, transmission=0.0, alpha=1.0):
    m, nt = _mat(name)
    b = _bsdf(nt)
    b.inputs['Base Color'].default_value = (*color, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    b.inputs['Transmission Weight'].default_value = transmission
    if emit:
        b.inputs['Emission Color'].default_value = (*emit, 1)
        b.inputs['Emission Strength'].default_value = emit_strength
    if alpha < 1.0:
        b.inputs['Alpha'].default_value = alpha
    return m


def mat_gold(name='DC_Gold', rough=0.42):
    """Warm gold, per-facet variation between rich and pale gold so instanced coins sparkle unevenly."""
    return mat_facet(name, (0.88, 0.55, 0.12), (1.0, 0.78, 0.32), rough=rough, metal=1.0)


def mat_gem(name, color):
    """Cut jewel: deep, not candy-bright colour, a little transmission and a hard specular glint."""
    m = mat_simple(name, color, rough=0.03, transmission=0.3)
    b = _bsdf(m.node_tree)
    b.inputs['IOR'].default_value = 2.2
    b.inputs['Specular IOR Level'].default_value = 1.0
    return m


def mat_sky(name='DC_Sky', sun_xy=(-0.77, 0.64)):
    """Sky seen through the hole: warm glow on the sun side fading to a cool blue, with soft cloud breakup,
    dim enough that the hole keeps a gradient instead of a blown disc."""
    m, nt = _mat(name)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    dot = nt.nodes.new('ShaderNodeVectorMath')
    dot.operation = 'DOT_PRODUCT'
    dot.inputs[1].default_value = (sun_xy[0], sun_xy[1], 0)
    nt.links.new(tc.outputs['Object'], dot.inputs[0])
    nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value, nz.inputs['Detail'].default_value = 0.12, 3.0
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    add = nt.nodes.new('ShaderNodeMath')
    add.operation = 'MULTIPLY_ADD'                             # sun side + (noise - 0.5) * 6 m of cloud breakup
    nt.links.new(nz.outputs['Fac'], add.inputs[0])
    add.inputs[1].default_value, add.inputs[2].default_value = 6.0, -3.0
    s = nt.nodes.new('ShaderNodeMath')
    s.operation = 'ADD'
    nt.links.new(dot.outputs['Value'], s.inputs[0])
    nt.links.new(add.outputs[0], s.inputs[1])
    mr = nt.nodes.new('ShaderNodeMapRange')
    mr.inputs['From Min'].default_value, mr.inputs['From Max'].default_value = -12.0, 18.0
    nt.links.new(s.outputs[0], mr.inputs['Value'])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (0.10, 0.16, 0.30, 1)  # cool sky away from the sun
    ramp.color_ramp.elements[1].color = (0.75, 0.58, 0.40, 1)  # warm glow towards the sun
    nt.links.new(mr.outputs['Result'], ramp.inputs[0])
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Strength'].default_value = 0.5
    nt.links.new(ramp.outputs['Color'], em.inputs['Color'])
    nt.links.new(em.outputs[0], out.inputs['Surface'])
    return m


def materials():
    """All shared materials, created once per build (names are stable, so rebuilds reuse them)."""
    return dict(
        rock=mat_facet('DC_Rock', (0.075, 0.068, 0.066), (0.20, 0.175, 0.16), rough=0.92,
                       c_alt=(0.035, 0.06, 0.025), alt_amount=0.0),
        rock_moss=mat_facet('DC_RockMoss', (0.075, 0.068, 0.066), (0.20, 0.175, 0.16), rough=0.92,
                            c_alt=(0.035, 0.07, 0.022), alt_amount=0.45),
        floor=mat_facet('DC_Floor', (0.09, 0.075, 0.065), (0.21, 0.17, 0.14), rough=0.9),
        stone=mat_facet('DC_CarvedStone', (0.22, 0.20, 0.18), (0.40, 0.36, 0.31), rough=0.85,
                        c_alt=(0.08, 0.14, 0.05), alt_amount=0.12),
        gold=mat_gold(),
        gold_mound=mat_gold('DC_GoldMound', rough=0.38),
        bone=mat_facet('DC_Bone', (0.55, 0.48, 0.36), (0.78, 0.71, 0.58), rough=0.7),
        moss=mat_facet('DC_Moss', (0.04, 0.09, 0.025), (0.13, 0.24, 0.05), rough=0.95),
        leaf=mat_facet('DC_Leaf', (0.05, 0.13, 0.03), (0.16, 0.32, 0.07), rough=0.7),
        gem_red=mat_gem('DC_GemRed', (0.30, 0.012, 0.03)),
        gem_green=mat_gem('DC_GemGreen', (0.015, 0.20, 0.07)),
        gem_blue=mat_gem('DC_GemBlue', (0.02, 0.05, 0.30)),
        sky=mat_sky(),
    )


def jitter(v, rng, a):
    return v + Vector(((rng.random() - .5) * a, (rng.random() - .5) * a, (rng.random() - .5) * a))
