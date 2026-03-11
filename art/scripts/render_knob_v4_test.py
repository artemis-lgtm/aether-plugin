"""
Blender knob v4 test - 3 frames only for rapid iteration
Change: colored indicator (coral orange), wider, with glow
"""

import bpy
import math
import os

TEST_FRAMES = list(range(128))  # full render
FRAME_SIZE = 256
OUTPUT_DIR = '/tmp/aether-art/knob_v4d_full'
os.makedirs(OUTPUT_DIR, exist_ok=True)

TOTAL_FRAMES = 128  # for angle calculation

bpy.ops.wm.read_factory_settings(use_empty=True)

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 64
scene.render.resolution_x = FRAME_SIZE
scene.render.resolution_y = FRAME_SIZE
scene.render.film_transparent = True
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'

# World lighting
world = bpy.data.worlds.new('World')
scene.world = world
world.use_nodes = True
wn = world.node_tree.nodes
wl = world.node_tree.links
wn.clear()
bg = wn.new('ShaderNodeBackground')
bg.inputs['Strength'].default_value = 2.5
bg.inputs['Color'].default_value = (0.92, 0.90, 0.87, 1.0)
output = wn.new('ShaderNodeOutputWorld')
wl.new(bg.outputs['Background'], output.inputs['Surface'])

# === KNOB GEOMETRY ===

# Skirt (darker base)
bpy.ops.mesh.primitive_cylinder_add(radius=0.50, depth=0.08, location=(0, 0, 0.04), vertices=64)
skirt = bpy.context.active_object
skirt.name = 'Skirt'

# Body
bpy.ops.mesh.primitive_cylinder_add(radius=0.44, depth=0.22, location=(0, 0, 0.19), vertices=64)
body = bpy.context.active_object
body.name = 'Body'
bpy.ops.object.modifier_add(type='BEVEL')
body.modifiers['Bevel'].width = 0.025
body.modifiers['Bevel'].segments = 3
bpy.ops.object.modifier_apply(modifier='Bevel')

# Dome cap
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.44, location=(0, 0, 0.30), segments=64, ring_count=32)
cap = bpy.context.active_object
cap.name = 'Cap'
cap.scale[2] = 0.18

# INDICATOR BAR - wider, extends from center to near rim
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.20, 0.375))
indicator_bar = bpy.context.active_object
indicator_bar.name = 'IndicatorBar'
indicator_bar.scale = (0.08, 0.24, 0.025)  # VERY wide + long

# INDICATOR DOT - large colored dot at tip
bpy.ops.mesh.primitive_cylinder_add(radius=0.09, depth=0.035, location=(0, 0.38, 0.37), vertices=32)
indicator_dot = bpy.context.active_object
indicator_dot.name = 'IndicatorDot'

# Concentric groove
bpy.ops.mesh.primitive_torus_add(major_radius=0.30, minor_radius=0.008, location=(0, 0, 0.35), major_segments=64, minor_segments=8)
groove = bpy.context.active_object
groove.name = 'Groove'

# === MATERIALS ===

# White glossy plastic
mat_white = bpy.data.materials.new('WhitePlastic')
mat_white.use_nodes = True
tree = mat_white.node_tree
tree.nodes.clear()
out_m = tree.nodes.new('ShaderNodeOutputMaterial')
bsdf = tree.nodes.new('ShaderNodeBsdfPrincipled')
bsdf.inputs['Base Color'].default_value = (0.95, 0.94, 0.93, 1.0)
bsdf.inputs['Roughness'].default_value = 0.08
bsdf.inputs['Specular IOR Level'].default_value = 0.7
bsdf.inputs['Coat Weight'].default_value = 0.5
bsdf.inputs['Coat Roughness'].default_value = 0.02
tree.links.new(bsdf.outputs['BSDF'], out_m.inputs['Surface'])

body.data.materials.append(mat_white)
cap.data.materials.append(mat_white)

# Darker skirt
mat_skirt = bpy.data.materials.new('Skirt')
mat_skirt.use_nodes = True
s = mat_skirt.node_tree.nodes['Principled BSDF']
s.inputs['Base Color'].default_value = (0.72, 0.70, 0.67, 1.0)
s.inputs['Roughness'].default_value = 0.2
s.inputs['Metallic'].default_value = 0.3
skirt.data.materials.append(mat_skirt)

# CORAL ORANGE indicator bar  
mat_coral = bpy.data.materials.new('CoralIndicator')
mat_coral.use_nodes = True
tree_c = mat_coral.node_tree
tree_c.nodes.clear()
out_c = tree_c.nodes.new('ShaderNodeOutputMaterial')
bsdf_c = tree_c.nodes.new('ShaderNodeBsdfPrincipled')
bsdf_c.inputs['Base Color'].default_value = (0.005, 0.005, 0.005, 1.0)  # absolute black
bsdf_c.inputs['Roughness'].default_value = 0.95  # fully matte, no specular bounce
bsdf_c.inputs['Specular IOR Level'].default_value = 0.0  # kill specular
bsdf_c.inputs['Emission Strength'].default_value = 0.0
tree_c.links.new(bsdf_c.outputs['BSDF'], out_c.inputs['Surface'])

indicator_bar.data.materials.append(mat_coral)
indicator_dot.data.materials.append(mat_coral)

# Groove
mat_groove = bpy.data.materials.new('Groove')
mat_groove.use_nodes = True
g = mat_groove.node_tree.nodes['Principled BSDF']
g.inputs['Base Color'].default_value = (0.80, 0.78, 0.76, 1.0)
g.inputs['Roughness'].default_value = 0.3
groove.data.materials.append(mat_groove)

# === PARENT ===
bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
pivot = bpy.context.active_object
pivot.name = 'KnobPivot'
for obj in [skirt, body, cap, indicator_bar, indicator_dot, groove]:
    obj.parent = pivot

# Shadow catcher
bpy.ops.mesh.primitive_plane_add(size=5, location=(0, 0, 0))
sp = bpy.context.active_object
sp.is_shadow_catcher = True

# Camera
bpy.ops.object.camera_add(location=(0, 0, 4))
cam = bpy.context.active_object
cam.data.type = 'ORTHO'
cam.data.ortho_scale = 1.3
cam.rotation_euler = (0, 0, 0)
scene.camera = cam

# Lighting
bpy.ops.object.light_add(type='AREA', location=(0.8, -0.6, 3.0))
k = bpy.context.active_object; k.data.energy = 50; k.data.size = 2.5

bpy.ops.object.light_add(type='AREA', location=(-0.9, 0.2, 2.5))
f = bpy.context.active_object; f.data.energy = 25; f.data.size = 2.0

bpy.ops.object.light_add(type='AREA', location=(0, 0, 5.0))
o = bpy.context.active_object; o.data.energy = 35; o.data.size = 1.5

bpy.ops.object.light_add(type='AREA', location=(0, 1.0, 2.0))
r = bpy.context.active_object; r.data.energy = 15; r.data.size = 1.0

# === RENDER TEST FRAMES ===
for i in TEST_FRAMES:
    angle = math.radians(-135 + (i / (TOTAL_FRAMES - 1)) * 270)
    pivot.rotation_euler[2] = angle
    bpy.context.view_layer.update()
    scene.render.filepath = os.path.join(OUTPUT_DIR, f'frame_{i:04d}.png')
    bpy.ops.render.render(write_still=True)
    print(f"Rendered frame {i}")

print("DONE: 3 test frames rendered")
