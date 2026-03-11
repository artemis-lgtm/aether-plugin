import bpy, bmesh, math, os

# Minimal scene
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# Simple box like the pedal
bpy.ops.mesh.primitive_cube_add(size=1, location=(0,0,0.6))
obj = bpy.context.active_object
obj.scale = (3.5, 2.0, 0.6)
bpy.ops.object.transform_apply(scale=True)

# Bevel
bpy.ops.object.modifier_add(type='BEVEL')
obj.modifiers['Bevel'].width = 0.14
obj.modifiers['Bevel'].segments = 4
obj.modifiers['Bevel'].limit_method = 'ANGLE'
obj.modifiers['Bevel'].angle_limit = math.radians(30)
bpy.ops.object.modifier_apply(modifier='Bevel')

# 3 debug materials: RED=top, BLUE=sides, GREEN=bottom
colors = [(1,0,0,1), (0,0,1,1), (0,1,0,1)]
names = ['Top_RED', 'Side_BLUE', 'Bottom_GREEN']
for name, color in zip(names, colors):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = color
    mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.8
    obj.data.materials.append(mat)

# Assign materials like the real script
bpy.ops.object.mode_set(mode='EDIT')
bm = bmesh.from_edit_mesh(obj.data)
bm.faces.ensure_lookup_table()

top_count = side_count = bottom_count = 0
for face in bm.faces:
    if face.normal.z > 0.5:
        face.material_index = 0
        top_count += 1
    elif face.normal.z < -0.5:
        face.material_index = 2
        bottom_count += 1
    else:
        face.material_index = 1
        side_count += 1

bmesh.update_edit_mesh(obj.data)
bpy.ops.object.mode_set(mode='OBJECT')

print(f"FACE COUNTS: top={top_count}, sides={side_count}, bottom={bottom_count}")
print(f"TOTAL: {top_count + side_count + bottom_count}")

# Camera
from mathutils import Vector
bpy.ops.object.camera_add(location=(1.5, -3.0, 4.5))
cam = bpy.context.active_object
cam.data.type = 'PERSP'
cam.data.lens = 50
target = Vector((0, 0, 0.4))
direction = target - cam.location
rot = direction.to_track_quat('-Z', 'Y')
cam.rotation_euler = rot.to_euler()
scene.camera = cam

# Simple light
bpy.ops.object.light_add(type='SUN', location=(0,0,5))
bpy.context.active_object.data.energy = 3

# Render
scene.render.resolution_x = 512
scene.render.resolution_y = 320
scene.render.engine = 'CYCLES'
scene.cycles.samples = 16
scene.render.filepath = '/tmp/aether-art/debug_materials.png'
bpy.ops.render.render(write_still=True)
print("DONE: debug render saved")
