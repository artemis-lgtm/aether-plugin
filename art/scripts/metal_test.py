import bpy, math
from mathutils import Vector

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# Simple beveled box
bpy.ops.mesh.primitive_cube_add(size=2, location=(0,0,1))
obj = bpy.context.active_object
obj.scale = (2, 1.2, 0.5)
bpy.ops.object.transform_apply(scale=True)

bpy.ops.object.modifier_add(type='BEVEL')
obj.modifiers['Bevel'].width = 0.15
obj.modifiers['Bevel'].segments = 3
bpy.ops.object.modifier_apply(modifier='Bevel')

# CHROME material -- should be unmistakably metallic
mat = bpy.data.materials.new('Chrome')
mat.use_nodes = True
bsdf = mat.node_tree.nodes['Principled BSDF']
bsdf.inputs['Base Color'].default_value = (0.8, 0.82, 0.85, 1.0)
bsdf.inputs['Metallic'].default_value = 1.0
bsdf.inputs['Roughness'].default_value = 0.05  # near mirror
obj.data.materials.append(mat)

# Floor
bpy.ops.mesh.primitive_plane_add(size=20, location=(0,0,0))
floor = bpy.context.active_object
fmat = bpy.data.materials.new('Floor')
fmat.use_nodes = True
fmat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.1, 0.07, 0.05, 1)
fmat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.5
floor.data.materials.append(fmat)

# HDRI environment
world = bpy.data.worlds.new('World')
scene.world = world
world.use_nodes = True
wn = world.node_tree.nodes
wl = world.node_tree.links
for n in wn: wn.remove(n)

env = wn.new('ShaderNodeTexEnvironment')
env.image = bpy.data.images.load('/tmp/aether-art/studio.hdr')
bg = wn.new('ShaderNodeBackground')
bg.inputs['Strength'].default_value = 4.0
out = wn.new('ShaderNodeOutputWorld')
wl.new(env.outputs['Color'], bg.inputs['Color'])
wl.new(bg.outputs['Background'], out.inputs['Surface'])
print(f"HDRI loaded: {env.image.name}, size={env.image.size[0]}x{env.image.size[1]}")

# Camera
bpy.ops.object.camera_add(location=(1.5, -2.5, 3.0))
cam = bpy.context.active_object
cam.data.type = 'PERSP'
cam.data.lens = 50
target = Vector((0, 0, 0.8))
direction = target - cam.location
rot = direction.to_track_quat('-Z', 'Y')
cam.rotation_euler = rot.to_euler()
scene.camera = cam

# Render
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 64
scene.render.resolution_x = 512
scene.render.resolution_y = 320
scene.render.filepath = '/tmp/aether-art/metal_test.png'
bpy.ops.render.render(write_still=True)
print("DONE: metal test")
