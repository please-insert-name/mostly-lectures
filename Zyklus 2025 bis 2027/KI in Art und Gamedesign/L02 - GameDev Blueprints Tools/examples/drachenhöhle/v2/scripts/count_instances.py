import bpy, collections
dg = bpy.context.evaluated_depsgraph_get()
cnt = collections.Counter(inst.object.name for inst in dg.object_instances if inst.is_instance)
print(cnt.most_common(6))
