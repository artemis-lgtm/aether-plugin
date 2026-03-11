"""
Blender script to render a photorealistic white guitar pedal knob filmstrip.
Run with: blender --background --python render_knob.py

Creates 128 frames of a white plastic knob rotating from -135° to +135°,
rendered with orthographic camera, HDRI lighting, transparent background,
and shadow catcher plane.
"""

import bpy
import math
import os

FRAMES = 128
FRAME_SIZE = 256  # render resolution per frame
OUTPUT_DIR = '/tmp/aether-art/knob_frames'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================
# Clean scene
# ============================================================
bpy.ops.wm.read_factory_settings(use_empty=True)

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 64  # good enough for small knob
scene.render.resolution_x = FRAME_SIZE
scene.render.resolution_y = FRAME_SIZE
scene.render.film_transparent = True  # transparent background
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'

# ============================================================
# HDRI World Lighting (use a neutral studio-like setup)
# ============================================================
world = bpy.data.worlds.new('World')
scene.world = world
world.use_nodes = True
nodes = world.node_tree.nodes
links = world.node_tree.links
nodes.clear()

# Background node with warm studio light
bg = nodes.new('ShaderNodeBackground')
bg.inputs['Strength'].default_value = 2.0
bg.inputs['Color'].default_value = (0.95, 0.93, 0.90, 1.0)  # warm white

output = nodes.new('ShaderNodeOutputWorld')
links.new(bg.outputs['Background'], output.inputs['Surface'])

# ============================================================
# Create the knob geometry
# ============================================================

# Base cylinder (knob body)
bpy.ops.mesh.primitive_cylinder_add(
    radius=0.4, depth=0.25, location=(0, 0, 0.125),
    vertices=64
)
knob_body = bpy.context.active_object
knob_body.name = 'KnobBody'

# Top dome (cap)
bpy.ops.mesh.primitive_uv_sphere_add(
    radius=0.38, location=(0, 0, 0.25),
    segments=64, ring_count=32
)
knob_cap = bpy.context.active_object
knob_cap.name = 'KnobCap'

# Scale the cap to make it a shallow dome
knob_cap.scale[2] = 0.3

# Indicator line (thin dark strip on top)
bpy.ops.mesh.primitive_cube_add(
    size=1, location=(0, 0.18, 0.36)
)
indicator = bpy.context.active_object
indicator.name = 'Indicator'
indicator.scale = (0.015, 0.12, 0.008)

# Grip ridges around the body (subtle ring)
bpy.ops.mesh.primitive_torus_add(
    major_radius=0.41, minor_radius=0.015,
    location=(0, 0, 0.12),
    major_segments=64, minor_segments=12
)
grip = bpy.context.active_object
grip.name = 'Grip'

# ============================================================
# Materials
# ============================================================

# White glossy plastic for knob body and cap
mat_white = bpy.data.materials.new('WhitePlastic')
mat_white.use_nodes = True
bsdf = mat_white.node_tree.nodes['Principled BSDF']
bsdf.inputs['Base Color'].default_value = (0.92, 0.91, 0.89, 1.0)
bsdf.inputs['Roughness'].default_value = 0.15
bsdf.inputs['Specular IOR Level'].default_value = 0.5

knob_body.data.materials.append(mat_white)
knob_cap.data.materials.append(mat_white)
grip.data.materials.append(mat_white)

# Dark indicator material
mat_dark = bpy.data.materials.new('DarkIndicator')
mat_dark.use_nodes = True
bsdf_dark = mat_dark.node_tree.nodes['Principled BSDF']
bsdf_dark.inputs['Base Color'].default_value = (0.05, 0.05, 0.05, 1.0)
bsdf_dark.inputs['Roughness'].default_value = 0.3

indicator.data.materials.append(mat_dark)

# ============================================================
# Parent all parts to an empty (rotation pivot)
# ============================================================
bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
pivot = bpy.context.active_object
pivot.name = 'KnobPivot'

for obj in [knob_body, knob_cap, indicator, grip]:
    obj.parent = pivot

# ============================================================
# Shadow catcher plane
# ============================================================
bpy.ops.mesh.primitive_plane_add(size=3, location=(0, 0, 0))
shadow_plane = bpy.context.active_object
shadow_plane.name = 'ShadowCatcher'
shadow_plane.is_shadow_catcher = True

# ============================================================
# Camera (orthographic, top-down)
# ============================================================
bpy.ops.object.camera_add(location=(0, 0, 3))
camera = bpy.context.active_object
camera.name = 'TopDownCam'
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 1.1  # frame the knob snugly
camera.rotation_euler = (0, 0, 0)  # looking straight down
scene.camera = camera

# ============================================================
# Lighting (3-point for realism)
# ============================================================
# Key light (top-right)
bpy.ops.object.light_add(type='AREA', location=(0.5, -0.5, 2.5))
key = bpy.context.active_object
key.data.energy = 30
key.data.size = 1.5

# Fill light (left)
bpy.ops.object.light_add(type='AREA', location=(-0.8, 0.3, 2.0))
fill = bpy.context.active_object
fill.data.energy = 15
fill.data.size = 1.5

# Rim/back light (behind)
bpy.ops.object.light_add(type='AREA', location=(0, 1.0, 1.5))
rim = bpy.context.active_object
rim.data.energy = 10
rim.data.size = 1.0

# ============================================================
# Render 128 frames
# ============================================================
for i in range(FRAMES):
    # Rotation from -135° to +135° (270° sweep)
    angle = math.radians(-135 + (i / (FRAMES - 1)) * 270)
    pivot.rotation_euler[2] = angle
    
    # Update scene
    bpy.context.view_layer.update()
    
    # Set output path
    scene.render.filepath = os.path.join(OUTPUT_DIR, f'frame_{i:04d}.png')
    
    # Render
    bpy.ops.render.render(write_still=True)

print(f"DONE: Rendered {FRAMES} frames to {OUTPUT_DIR}")
