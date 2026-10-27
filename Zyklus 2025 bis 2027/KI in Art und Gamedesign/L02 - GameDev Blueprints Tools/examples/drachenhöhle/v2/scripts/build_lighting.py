"""Step 5: golden-hour lighting, haze volume, dust motes in the sun beam, EEVEE render settings.

Day lighting per the skill: a warm sun through the ceiling hole is the key, a cool sky fill falls through the same
hole, warm bounce from the gold lifts the dragon's underside, and a bounded haze volume makes the beam visible."""
import bpy, bmesh, os, sys, random, math, importlib
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import layout as L, dc
importlib.reload(L); importlib.reload(dc)

rng = random.Random(L.SEED + 5)
scene = bpy.data.scenes.get('Scene') or bpy.context.scene
col = dc.coll('05_Lighting')
dc.clear(col)
HOLE = Vector((L.HOLE_XY[0], L.HOLE_XY[1], 24.0))
TARGET = Vector(L.SUN_TARGET)


def light(name, kind, loc, energy, color, aim=None, size=None, shadow=True, **kw):
    ld = bpy.data.lights.get(name) or bpy.data.lights.new(name, kind)
    if ld.type != kind:
        ld.type = kind
    ld.energy, ld.color, ld.use_shadow = energy, color, shadow
    if size is not None:
        if kind == 'AREA':
            ld.shape, ld.size = 'DISK', size
        elif kind == 'SUN':
            ld.angle = size
        else:
            ld.shadow_soft_size = size
    for k, v in kw.items():
        setattr(ld, k, v)
    ob = bpy.data.objects.new(name, ld)
    ob.location = loc
    if aim is not None:
        ob.rotation_euler = (Vector(aim) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    col.objects.link(ob)
    return ob


# key: golden-hour sun through the hole
sun_dir = (TARGET - HOLE).normalized()
light('Sun_Golden', 'SUN', HOLE - sun_dir * 6, L.SUN_STRENGTH, L.SUN_COLOR, aim=HOLE,
      size=math.radians(1.2), volume_factor=3.0)   # beam stronger in the haze only
# sky light falling through the hole (cool), and a weak cool fill from the open side of the cave
light('Sky_Fill', 'AREA', HOLE + Vector((0, 0, -1.0)), 3500, (0.64, 0.75, 0.95), aim=HOLE + Vector((0, 0, -10)), size=7.0)
light('Cave_Fill', 'AREA', (-6.0, -12.0, 11.0), 1600, (0.60, 0.68, 0.78), aim=(0.5, 4.0, 3.0), size=14.0, shadow=False)
# warm bounce from the gold onto the dragon's belly and the cave walls
light('Gold_Bounce', 'AREA', (L.HOARD_XY[0], L.HOARD_XY[1] - 2.0, 3.2), 1200, (1.0, 0.62, 0.25),
      aim=(L.HOARD_XY[0], L.HOARD_XY[1] - 2.0, 10.0), size=9.0, shadow=False)

# world: near-black, slightly cool; the teal in the shadows comes from the grade (lift), not the light,
# so metallic gold does not reflect blue and turn olive
w = scene.world or bpy.data.worlds.new('DC_World')
scene.world = w
w.use_nodes = True
bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')
bg.inputs['Color'].default_value = (0.020, 0.024, 0.029, 1)
bg.inputs['Strength'].default_value = 1.0
out = next(n for n in w.node_tree.nodes if n.type == 'OUTPUT_WORLD')
for lk in list(out.inputs['Volume'].links):          # a world volume would extinguish the sun in EEVEE
    w.node_tree.links.remove(lk)

# bounded haze inside the cave
bm = bmesh.new()
bmesh.ops.create_cube(bm, size=1.0)
haze = dc.bm_to_obj(bm, 'Haze_Volume', col, [], var=0.0, loc=(0.0, 2.0, 12.5))
haze.scale = (52, 56, 25)
m = bpy.data.materials.get('DC_Haze') or bpy.data.materials.new('DC_Haze')
m.use_nodes = True
nt = m.node_tree
nt.nodes.clear()
vol = nt.nodes.new('ShaderNodeVolumePrincipled')
vol.inputs['Density'].default_value = 0.005
vol.inputs['Anisotropy'].default_value = 0.55
vol.inputs['Color'].default_value = (0.95, 0.9, 0.85, 1)
o = nt.nodes.new('ShaderNodeOutputMaterial')
nt.links.new(vol.outputs[0], o.inputs['Volume'])
haze.data.materials.append(m)
haze.visible_shadow = False

# denser haze only along the sun shaft: the beam reads as a hard warm column instead of a grey wash
bm = bmesh.new()
length = (TARGET - HOLE).length + 6.0
bmesh.ops.create_cone(bm, cap_ends=True, segments=48, radius1=L.HOLE_R * 1.25, radius2=L.HOLE_R * 1.25, depth=length)
beam = dc.bm_to_obj(bm, 'Beam_Haze', col, [], var=0.0)
beam.location = HOLE + sun_dir * (length / 2 - 1.0)
beam.rotation_euler = sun_dir.to_track_quat('Z', 'Y').to_euler()
mb = bpy.data.materials.get('DC_BeamHaze') or bpy.data.materials.new('DC_BeamHaze')
mb.use_nodes = True
nt = mb.node_tree
nt.nodes.clear()
vb = nt.nodes.new('ShaderNodeVolumePrincipled')
# soft edge: density fades out towards the cylinder wall, so the shaft has no hard (stepped) outline
tc = nt.nodes.new('ShaderNodeTexCoord')
sep = nt.nodes.new('ShaderNodeSeparateXYZ')
nt.links.new(tc.outputs['Object'], sep.inputs[0])
xy = nt.nodes.new('ShaderNodeCombineXYZ')
nt.links.new(sep.outputs['X'], xy.inputs['X'])
nt.links.new(sep.outputs['Y'], xy.inputs['Y'])
rad = nt.nodes.new('ShaderNodeVectorMath')
rad.operation = 'LENGTH'
nt.links.new(xy.outputs[0], rad.inputs[0])
edge = nt.nodes.new('ShaderNodeMapRange')
edge.interpolation_type = 'SMOOTHSTEP'
edge.inputs['From Min'].default_value, edge.inputs['From Max'].default_value = L.HOLE_R * 0.6, L.HOLE_R * 1.2
edge.inputs['To Min'].default_value, edge.inputs['To Max'].default_value = 0.026, 0.0
nt.links.new(rad.outputs['Value'], edge.inputs['Value'])
nt.links.new(edge.outputs['Result'], vb.inputs['Density'])
vb.inputs['Anisotropy'].default_value = 0.4    # less glare when looking up the shaft
vb.inputs['Color'].default_value = (1.0, 0.95, 0.88, 1)
ob = nt.nodes.new('ShaderNodeOutputMaterial')
nt.links.new(vb.outputs[0], ob.inputs['Volume'])
beam.data.materials.append(mb)
beam.visible_shadow = False

# dust motes drifting inside the sun beam
bm = bmesh.new()
up = Vector((0, 0, 1))
side = sun_dir.cross(up).normalized()
side2 = sun_dir.cross(side).normalized()
length = (TARGET - HOLE).length
for _ in range(380):
    t = rng.random() ** 0.8
    a, rr = rng.random() * 6.283, L.HOLE_R * 0.8 * math.sqrt(rng.random())
    c = HOLE + sun_dir * (t * length * 1.05) + side * math.cos(a) * rr + side2 * math.sin(a) * rr
    s = 0.008 + rng.random() ** 4 * 0.025
    vs = [bm.verts.new(c + Vector(d) * s) for d in ((1, 0, -.4), (-.5, .87, -.4), (-.5, -.87, -.4), (0, 0, 1))]
    for f in ((0, 1, 2), (0, 3, 1), (1, 3, 2), (2, 3, 0)):
        bm.faces.new([vs[i] for i in f])
dust = dc.bm_to_obj(bm, 'Dust_Motes', col, [dc.mat_simple('DC_Dust', (1.0, 0.8, 0.5), emit=(1.0, 0.72, 0.42), emit_strength=1.5)])
dust.visible_shadow = False

# ---------------------------------------------------------------- EEVEE settings
try:
    scene.render.engine = 'BLENDER_EEVEE'
except TypeError as e:
    print('engine:', e)
ee = scene.eevee
ee.use_shadows = True
ee.shadow_pool_size = '1024'
ee.use_volumetric_shadows = True
ee.volumetric_tile_size = '4'          # 8 showed banding rings in the haze
ee.volumetric_samples = 96
ee.volumetric_start, ee.volumetric_end = 0.5, 90.0
ee.use_raytracing = True
ee.ray_tracing_method = 'SCREEN'
ee.fast_gi_method = 'GLOBAL_ILLUMINATION'
scene.render.film_transparent = False
vs = scene.view_settings
try:                               # hue-preserving: AgX turned the sunlit red dragon and the gold pink
    vs.view_transform = 'Khronos PBR Neutral'
except TypeError as e:
    print('view transform:', e)
vs.look = 'None'
vs.exposure = 0.0
print('lighting ok: sun elevation', round(math.degrees(math.asin(-sun_dir.z)), 1), 'deg, look', vs.look)
