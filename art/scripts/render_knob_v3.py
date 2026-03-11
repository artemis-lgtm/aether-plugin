"""
Blender knob v3 - Bold, high-contrast white plastic knob
Focus: indicator visibility at 62px, proper specular, HDRI lighting
"""

import bpy
import bmesh
import math
import os
import mathutils

FRAMES = 128
FRAME_SIZE = 256  # fast render, downscale to 64 for JUCE
OUTPUT_DIR = '/tmp/aether-art/knob_frames_v3'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Clean scene
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

# World: gradient dome lighting
world = bpy.data.worlds.new('World')
scene.world = world
world.use_nodes = True
wn = world.node_tree.nodes
wl = world.node_tree.links
wn.clear()

# Create gradient: bright top, warm sides
texcoord = wn.new('ShaderNodeTexCoord')
mapping = wn.new('ShaderNodeMapping')
gradient = wn.new('ShaderNodeTexGradient')
gradient.gradient_type = 'SPHERICAL'
colorramp = wn.new('ShaderNodeValToRGB')
colorramp.color_ramp.elements[0].color = (0.3, 0.28, 0.25, 1.0)  # warm shadow
colorramp.color_ramp.elements[1].color = (1.0, 0.98, 0.95, 1.0)  # bright highlight
bg = wn.new('ShaderNodeBackground')
bg.inputs['Strength'].default_value = 3.0
output = wn.new('ShaderNodeOutputWorld')

wl.new(texcoord.outputs['Generated'], mapping.inputs['Vector'])
wl.new(mapping.outputs['Vector'], gradient.inputs['Vector'])
wl.new(gradient.outputs['Color'], colorramp.inputs['Fac'])
wl.new(colorramp.outputs['Color'], bg.inputs['Color'])
wl.new(bg.outputs['Background'], output.inputs['Surface'])

# ============================================================
# KNOB GEOMETRY - chunky, clean, high-contrast
# ============================================================

# Darker skirt/base ring (wider, shorter)
bpy.ops.mesh.primitive_cylinder_add(
    radius=0.50, depth=0.08, location=(0, 0, 0.04), vertices=64
)
skirt = bpy.context.active_object
skirt.name = 'Skirt'

# Main body
bpy.ops.mesh.primitive_cylinder_add(
    radius=0.44, depth=0.22, location=(0, 0, 0.19), vertices=64
)
body = bpy.context.active_object
body.name = 'Body'

# Add bevel to body for soft edges
bpy.context.view_layer.objects.active = body
bpy.ops.object.modifier_add(type='BEVEL')
body.modifiers['Bevel'].width = 0.02
body.modifiers['Bevel'].segments = 3
bpy.ops.object.modifier_apply(modifier='Bevel')

# Top cap (flattened sphere dome)
bpy.ops.mesh.primitive_uv_sphere_add(
    radius=0.44, location=(0, 0, 0.30),
    segments=64, ring_count=32
)
cap = bpy.context.active_object
cap.name = 'Cap'
cap.scale[2] = 0.18

# BOLD INDICATOR - wide black stripe from center to rim
# This is THE most important element for readability
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.22, 0.37))
indicator_bar = bpy.context.active_object
indicator_bar.name = 'IndicatorBar'
indicator_bar.scale = (0.04, 0.22, 0.015)  # wide and long

# Indicator dot at tip (near rim, large enough to see at 62px)
bpy.ops.mesh.primitive_cylinder_add(
    radius=0.05, depth=0.02, location=(0, 0.38, 0.36),
    vertices=32
)
indicator_dot = bpy.context.active_object
indicator_dot.name = 'IndicatorDot'

# Concentric groove ring (decorative, adds realism)
bpy.ops.mesh.primitive_torus_add(
    major_radius=0.30, minor_radius=0.008,
    location=(0, 0, 0.35),
    major_segments=64, minor_segments=8
)
groove1 = bpy.context.active_object
groove1.name = 'Groove1'

# Outer edge highlight ring  
bpy.ops.mesh.primitive_torus_add(
    major_radius=0.445, minor_radius=0.005,
    location=(0, 0, 0.30),
    major_segments=64, minor_segments=8
)
edge_ring = bpy.context.active_object
edge_ring.name = 'EdgeRing'

# ============================================================
# MATERIALS
# ============================================================

# White glossy plastic (with clearcoat for that "polished" look)
mat_white = bpy.data.materials.new('WhitePlastic')
mat_white.use_nodes = True
tree = mat_white.node_tree
nodes = tree.nodes
links = tree.links
nodes.clear()

output_mat = nodes.new('ShaderNodeOutputMaterial')
principled = nodes.new('ShaderNodeBsdfPrincipled')
principled.inputs['Base Color'].default_value = (0.95, 0.94, 0.93, 1.0)
principled.inputs['Roughness'].default_value = 0.08  # very glossy
principled.inputs['Specular IOR Level'].default_value = 0.7
principled.inputs['Coat Weight'].default_value = 0.5
principled.inputs['Coat Roughness'].default_value = 0.02  # mirror clearcoat
links.new(principled.outputs['BSDF'], output_mat.inputs['Surface'])

body.data.materials.append(mat_white)
cap.data.materials.append(mat_white)

# Darker skirt material
mat_skirt = bpy.data.materials.new('SkirtMaterial')
mat_skirt.use_nodes = True
bsdf_s = mat_skirt.node_tree.nodes['Principled BSDF']
bsdf_s.inputs['Base Color'].default_value = (0.75, 0.73, 0.70, 1.0)
bsdf_s.inputs['Roughness'].default_value = 0.2
bsdf_s.inputs['Metallic'].default_value = 0.3  # slight metallic for rim feel
skirt.data.materials.append(mat_skirt)

# Bold black indicator
mat_black = bpy.data.materials.new('BlackIndicator')
mat_black.use_nodes = True
bsdf_b = mat_black.node_tree.nodes['Principled BSDF']
bsdf_b.inputs['Base Color'].default_value = (0.01, 0.01, 0.01, 1.0)
bsdf_b.inputs['Roughness'].default_value = 0.5
indicator_bar.data.materials.append(mat_black)
indicator_dot.data.materials.append(mat_black)

# Groove material (slightly recessed/darker)
mat_groove = bpy.data.materials.new('GrooveMaterial')
mat_groove.use_nodes = True
bsdf_g = mat_groove.node_tree.nodes['Principled BSDF']
bsdf_g.inputs['Base Color'].default_value = (0.80, 0.78, 0.76, 1.0)
bsdf_g.inputs['Roughness'].default_value = 0.3
groove1.data.materials.append(mat_groove)

# Bright edge highlight
mat_edge = bpy.data.materials.new('EdgeHighlight')
mat_edge.use_nodes = True
bsdf_e = mat_edge.node_tree.nodes['Principled BSDF']
bsdf_e.inputs['Base Color'].default_value = (1.0, 1.0, 1.0, 1.0)
bsdf_e.inputs['Roughness'].default_value = 0.05
bsdf_e.inputs['Metallic'].default_value = 0.5
edge_ring.data.materials.append(mat_edge)

# ============================================================
# Parent to pivot
# ============================================================
bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
pivot = bpy.context.active_object
pivot.name = 'KnobPivot'

for obj in [skirt, body, cap, indicator_bar, indicator_dot, groove1, edge_ring]:
    obj.parent = pivot

# ============================================================
# Shadow catcher
# ============================================================
bpy.ops.mesh.primitive_plane_add(size=5, location=(0, 0, 0))
shadow_plane = bpy.context.active_object
shadow_plane.name = 'ShadowCatcher'
shadow_plane.is_shadow_catcher = True

# ============================================================
# Camera (orthographic, straight down)
# ============================================================
bpy.ops.object.camera_add(location=(0, 0, 4))
camera = bpy.context.active_object
camera.name = 'TopCam'
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 1.3
camera.rotation_euler = (0, 0, 0)
scene.camera = camera

# ============================================================
# LIGHTING - dramatic studio setup
# ============================================================

# Main key (large softbox, upper right)
bpy.ops.object.light_add(type='AREA', location=(0.8, -0.6, 3.0))
key = bpy.context.active_object
key.data.energy = 50
key.data.size = 2.5
key.data.color = (1.0, 0.98, 0.96)
key.rotation_euler = (math.radians(15), math.radians(-10), 0)

# Fill (left, softer)
bpy.ops.object.light_add(type='AREA', location=(-0.9, 0.2, 2.5))
fill = bpy.context.active_object
fill.data.energy = 25
fill.data.size = 2.0
fill.data.color = (0.95, 0.97, 1.0)

# Overhead center (for dome highlight - crucial for specular)
bpy.ops.object.light_add(type='AREA', location=(0, 0, 5.0))
overhead = bpy.context.active_object
overhead.data.energy = 35
overhead.data.size = 1.5

# Back rim (for edge definition)
bpy.ops.object.light_add(type='AREA', location=(0, 1.0, 2.0))
rim = bpy.context.active_object
rim.data.energy = 15
rim.data.size = 1.0

# ============================================================
# RENDER
# ============================================================
for i in range(FRAMES):
    angle = math.radians(-135 + (i / (FRAMES - 1)) * 270)
    pivot.rotation_euler[2] = angle
    bpy.context.view_layer.update()
    scene.render.filepath = os.path.join(OUTPUT_DIR, f'frame_{i:04d}.png')
    bpy.ops.render.render(write_still=True)

print(f"DONE: Rendered {FRAMES} frames to {OUTPUT_DIR}")
