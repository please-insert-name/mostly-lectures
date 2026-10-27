"""Debug: how far the dragon's chin floats above (or sinks into) the gold."""
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
dg = bpy.context.evaluated_depsgraph_get()
mound = BVHTree.FromObject(bpy.data.objects['Hoard_Mound'], dg)
arm = bpy.data.objects['DragonArmature']
mw = arm.matrix_world
skull, snout = mw @ arm.pose.bones['SkullControl'].head, mw @ arm.pose.bones['Head.005'].head
me = bpy.data.objects['DragonMesh'].evaluated_get(dg)
head_vs = [me.matrix_world @ v.co for v in me.data.vertices if (me.matrix_world @ v.co - snout).length < 3.2]
low = min(head_vs, key=lambda p: p.z)
hit = mound.ray_cast(Vector((low.x, low.y, 40)), Vector((0, 0, -1)))
print('skull', tuple(round(v, 2) for v in skull), 'snout', tuple(round(v, 2) for v in snout))
print('chin', tuple(round(v, 2) for v in low), 'gold below at z', round(hit[0].z, 2) if hit[0] else None,
      '-> gap', round(low.z - hit[0].z, 2) if hit[0] else None)
