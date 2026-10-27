"""Step 5: light compositor finish: bloom on practicals, subtle lens dispersion, soft vignette."""
import bpy

scene = bpy.context.scene
old = bpy.data.node_groups.get('Cinematic_Comp')
if old:
    bpy.data.node_groups.remove(old)
t = bpy.data.node_groups.new('Cinematic_Comp', 'CompositorNodeTree')
t.interface.new_socket(name='Image', in_out='OUTPUT', socket_type='NodeSocketColor')
scene.compositing_node_group = t
scene.render.use_compositing = True
N, L = t.nodes, t.links

rl = N.new('CompositorNodeRLayers')
rl.location = (-800, 0)

glare = N.new('CompositorNodeGlare')
glare.location = (-550, 0)
glare.inputs['Type'].default_value = 'Bloom'
glare.inputs['Quality'].default_value = 'High'
glare.inputs['Threshold'].default_value = 1.2
glare.inputs['Strength'].default_value = 0.22
glare.inputs['Size'].default_value = 0.6
glare.inputs['Saturation'].default_value = 1.0
L.new(rl.outputs['Image'], glare.inputs['Image'])

lens = N.new('CompositorNodeLensdist')
lens.location = (-300, 0)
lens.inputs['Distortion'].default_value = 0.0
lens.inputs['Dispersion'].default_value = 0.008
lens.inputs['Fit'].default_value = True
L.new(glare.outputs['Image'], lens.inputs['Image'])

# vignette: blurred ellipse multiplied over the frame
ell = N.new('CompositorNodeEllipseMask')
ell.location = (-550, -350)
ell.inputs['Size'].default_value = (0.92, 0.82)
zero = N.new('ShaderNodeMath')          # zeroed copy of the frame gives the mask its canvas size
zero.location = (-800, -350)
zero.operation = 'MULTIPLY'
zero.inputs[1].default_value = 0.0
L.new(rl.outputs['Image'], zero.inputs[0])
L.new(zero.outputs[0], ell.inputs['Mask'])
blur = N.new('CompositorNodeBlur')
blur.location = (-300, -350)
blur.inputs['Size'].default_value = (260, 260)
L.new(ell.outputs['Mask'], blur.inputs['Image'])
mix = N.new('ShaderNodeMix')
mix.location = (-50, 0)
mix.data_type = 'RGBA'
mix.blend_type = 'MULTIPLY'
sock = {s.identifier: s for s in mix.inputs}
sock['Factor_Float'].default_value = 0.5
L.new(lens.outputs['Image'], sock['A_Color'])
L.new(blur.outputs['Image'], sock['B_Color'])
out = N.new('NodeGroupOutput')
out.location = (200, 0)
L.new([o for o in mix.outputs if o.identifier == 'Result_Color'][0], out.inputs[0])
print('compositor ok')
