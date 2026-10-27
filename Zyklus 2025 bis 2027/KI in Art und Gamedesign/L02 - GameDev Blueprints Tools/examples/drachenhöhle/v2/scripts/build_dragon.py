"""Step 3: the sleeping dragon ('Dragon Rigged' by na3ee1, CC-BY 3.0, Poly Pizza).
Placement and scale from layout.py, dark red / bronze faceted materials, eyes closed, then the sleeping pose."""
import bpy, os, sys, random, math, importlib
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import layout as L, dc
importlib.reload(L); importlib.reload(dc)

IMPORT_SCALE = 0.789924            # Poly Pizza normalisation of the import (12 m span in T-pose)
root = bpy.data.objects['Dragon_Root']
me = bpy.data.objects['DragonMesh']
root.location = L.DRAGON_LOC
root.rotation_euler = (0, 0, math.radians(L.DRAGON_ROT_Z))
root.scale = (IMPORT_SCALE * L.DRAGON_SCALE,) * 3

# per-face variation attribute on the imported mesh (same scheme as dc.bm_to_obj)
rng = random.Random(L.SEED + 3)
attr = me.data.color_attributes.get(dc.FV) or me.data.color_attributes.new(dc.FV, 'BYTE_COLOR', 'CORNER')
for poly in me.data.polygons:
    v, g = 0.5 + (rng.random() - .5) * 0.7, rng.random()
    for li in poly.loop_indices:
        attr.data[li].color = (v, g, 0.0, 1.0)
for poly in me.data.polygons:
    poly.use_smooth = False


def membrane(name):
    """Wing membrane: faceted bronze-red that glows warm when the sun shines through it."""
    m = dc.mat_facet(name, (0.07, 0.012, 0.006), (0.16, 0.035, 0.014), rough=0.75, spec=0.15)
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
    tr = nt.nodes.new('ShaderNodeBsdfTranslucent')
    tr.inputs['Color'].default_value = (0.6, 0.12, 0.03, 1)
    mix = nt.nodes.new('ShaderNodeMixShader')
    mix.inputs[0].default_value = 0.35
    nt.links.new(b.outputs[0], mix.inputs[1])
    nt.links.new(tr.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs['Surface'])
    return m


body = dc.mat_facet('DR_Body', (0.03, 0.003, 0.003), (0.095, 0.007, 0.005), rough=0.75, spec=0.15)   # deep red; a strong specular sheen in the sun reads pink
# by slot index (import order DarkGreen, Red, Yellow, Teeth, Green, Black), so rebuilds re-apply cleanly
NEW = [
    body,                                                                              # scales
    dc.mat_facet('DR_Mouth', (0.06, 0.01, 0.015), (0.12, 0.02, 0.03), rough=0.5),      # mouth
    dc.mat_facet('DR_Lid', (0.025, 0.006, 0.004), (0.05, 0.012, 0.008), rough=0.6),    # eyes: dark closed lids
    dc.mat_facet('DR_Teeth', (0.55, 0.47, 0.33), (0.75, 0.68, 0.52), rough=0.4),       # teeth and claws
    membrane('DR_Membrane'),                                                           # wing membranes
    dc.mat_facet('DR_Horn', (0.14, 0.09, 0.05), (0.36, 0.25, 0.13), rough=0.55),  # horns, spikes
]
for slot, mat in zip(me.material_slots, NEW):
    slot.material = mat
print('dragon slots', [s.material.name for s in me.material_slots])

path = os.path.join(HERE, 'pose_dragon.py')
exec(compile(open(path, encoding='utf-8').read(), path, 'exec'), {'__name__': '__main__', '__file__': path})
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
ev = me.evaluated_get(dg)
zs = [(ev.matrix_world @ v.co).z for v in ev.data.vertices]
print('dragon ok: z range', round(min(zs), 2), round(max(zs), 2), 'dims', tuple(round(d, 1) for d in ev.dimensions))

# ---------------------------------------------------------------- breath: a thin wisp of smoke from the nostrils
import bmesh
mw = ev.matrix_world
teeth = [mw @ p.center for p in ev.data.polygons if p.material_index == 3]
eye = [mw @ p.center for p in ev.data.polygons if p.material_index == 2][0]
snout = sum(teeth, Vector()) / len(teeth)
fwd = Vector(((snout - eye).x, (snout - eye).y, 0)).normalized()
nostril = snout + fwd * 0.4 + Vector((0, 0, 0.2))
col = dc.coll('10_Dragon')
old = bpy.data.objects.get('Nostril_Smoke')
if old:
    bpy.data.objects.remove(old)
bm = bmesh.new()
bmesh.ops.create_cube(bm, size=1.0)
smoke = dc.bm_to_obj(bm, 'Nostril_Smoke', col, [], var=0.0)
smoke.scale = (0.3, 0.3, 1.6)
smoke.location = nostril + fwd * 0.35 + Vector((0, -0.25, 0.65))
smoke.rotation_euler = (Vector((0, 0, 1)).rotation_difference((Vector((0, 0, 1)) + fwd * 0.5 + Vector((0, -0.35, 0))).normalized())).to_euler()
smoke.visible_shadow = False
m = bpy.data.materials.get('DR_Smoke') or bpy.data.materials.new('DR_Smoke')
m.use_nodes = True
nt = m.node_tree
nt.nodes.clear()
tc = nt.nodes.new('ShaderNodeTexCoord')
nz = nt.nodes.new('ShaderNodeTexNoise')
nz.inputs['Scale'].default_value, nz.inputs['Detail'].default_value = 3.5, 6.0
nz.inputs['Distortion'].default_value = 1.2              # curling wisps rather than a soft blob
nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
ramp = nt.nodes.new('ShaderNodeValToRGB')                      # wispy: only the noise peaks carry smoke
ramp.color_ramp.elements[0].position, ramp.color_ramp.elements[1].position = 0.6, 0.78
nt.links.new(nz.outputs['Fac'], ramp.inputs[0])
sep = nt.nodes.new('ShaderNodeSeparateXYZ')
nt.links.new(tc.outputs['Object'], sep.inputs[0])
fade = nt.nodes.new('ShaderNodeMapRange')                      # dense at the nostrils, gone at the top
fade.inputs['From Min'].default_value, fade.inputs['From Max'].default_value = -0.5, 0.5
fade.inputs['To Min'].default_value, fade.inputs['To Max'].default_value = 1.0, 0.0
nt.links.new(sep.outputs['Z'], fade.inputs['Value'])
rad = nt.nodes.new('ShaderNodeVectorMath')
rad.operation = 'LENGTH'
xy = nt.nodes.new('ShaderNodeCombineXYZ')
nt.links.new(sep.outputs['X'], xy.inputs['X'])
nt.links.new(sep.outputs['Y'], xy.inputs['Y'])
nt.links.new(xy.outputs[0], rad.inputs[0])
edge = nt.nodes.new('ShaderNodeMapRange')                      # soft round cross-section
edge.inputs['From Min'].default_value, edge.inputs['From Max'].default_value = 0.15, 0.5
edge.inputs['To Min'].default_value, edge.inputs['To Max'].default_value = 1.0, 0.0
nt.links.new(rad.outputs['Value'], edge.inputs['Value'])
m1 = nt.nodes.new('ShaderNodeMath')
m1.operation = 'MULTIPLY'
nt.links.new(ramp.outputs['Color'], m1.inputs[0])
nt.links.new(fade.outputs['Result'], m1.inputs[1])
m2 = nt.nodes.new('ShaderNodeMath')
m2.operation = 'MULTIPLY'
nt.links.new(m1.outputs[0], m2.inputs[0])
nt.links.new(edge.outputs['Result'], m2.inputs[1])
dens = nt.nodes.new('ShaderNodeMath')
dens.operation = 'MULTIPLY'
dens.inputs[1].default_value = 3.5
nt.links.new(m2.outputs[0], dens.inputs[0])
vol = nt.nodes.new('ShaderNodeVolumePrincipled')
vol.inputs['Color'].default_value = (0.72, 0.68, 0.64, 1)
nt.links.new(dens.outputs[0], vol.inputs['Density'])
out = nt.nodes.new('ShaderNodeOutputMaterial')
nt.links.new(vol.outputs[0], out.inputs['Volume'])
smoke.data.materials.append(m)
print('smoke at', tuple(round(v, 2) for v in nostril))
