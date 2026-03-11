"""
Blender script v2 - Photorealistic white guitar pedal knob
Fixes: bold indicator, specular highlights, dome curvature, grip texture
Run with: blender --background --python render_knob_v2.py
"""

import bpy
import bmesh
import math
import os

FRAMES = 128
FRAME_SIZE = 256
OUTPUT_DIR = '/tmp/aether-art/knob_frames_v2'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================
# Clean scene
# ============================================================
bpy.ops.wm.read_factory_settings(use_empty=True)

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 128  # higher quality
scene.render.resolution_x = FRAME_SIZE
scene.render.resolution_y = FRAME_SIZE
scene.render.film_transparent = True
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'

# ============================================================
# World: HDRI-like environment
# ============================================================
world = bpy.data.worlds.new('World')
scene.world = world
world.use_nodes = True
nodes = world.node_tree.nodes
links = world.node_tree.links
nodes.clear()

bg = nodes.new('ShaderNodeBackground')
bg.inputs['Strength'].default_value = 1.5
bg.inputs['Color'].default_value = (0.9, 0.88, 0.85, 1.0)
output = nodes.new('ShaderNodeOutputWorld')
links.new(bg.outputs['Background'], output.inputs['Surface'])

# ============================================================
# Create the knob
# ============================================================

# 1. Base skirt (wider bottom, like a real pot knob)
bpy.ops.mesh.primitive_cylinder_add(
    radius=0.44, depth=0.10, location=(0, 0, 0.05),
    vertices=64
)
skirt = bpy.context.active_object
skirt.name = 'Skirt'

# 2. Main body (slightly tapered cylinder)
bpy.ops.mesh.primitive_cone_add(
    radius1=0.40, radius2=0.36, depth=0.18,
    location=(0, 0, 0.19), vertices=64
)
body = bpy.context.active_object
body.name = 'Body'

# 3. Top dome (flattened sphere for convex cap)
bpy.ops.mesh.primitive_uv_sphere_add(
    radius=0.36, location=(0, 0, 0.28),
    segments=64, ring_count=32
)
cap = bpy.context.active_object
cap.name = 'Cap'
cap.scale[2] = 0.22  # flatten to dome

# 4. BOLD indicator notch - a black wedge/bar from center to rim
# Using a wider, more visible bar
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.15, 0.345))
indicator = bpy.context.active_object
indicator.name = 'Indicator'
indicator.scale = (0.025, 0.14, 0.012)  # wider and longer

# 5. Indicator dot at the end (near rim, very visible)
bpy.ops.mesh.primitive_cylinder_add(
    radius=0.03, depth=0.015, location=(0, 0.29, 0.34),
    vertices=32
)
dot = bpy.context.active_object
dot.name = 'IndicatorDot'

# 6. Grip ridges (multiple thin torus rings around body)
grip_rings = []
for i in range(8):
    z = 0.10 + i * 0.022
    bpy.ops.mesh.primitive_torus_add(
        major_radius=0.41 - i * 0.005,
        minor_radius=0.006,
        location=(0, 0, z),
        major_segments=64, minor_segments=8
    )
    ring = bpy.context.active_object
    ring.name = f'Grip_{i}'
    grip_rings.append(ring)

# ============================================================
# Materials
# ============================================================

# White glossy plastic (with slight warmth and specular)
mat_white = bpy.data.materials.new('WhitePlastic')
mat_white.use_nodes = True
tree = mat_white.node_tree
bsdf = tree.nodes['Principled BSDF']
bsdf.inputs['Base Color'].default_value = (0.93, 0.92, 0.90, 1.0)
bsdf.inputs['Roughness'].default_value = 0.12  # glossy!
bsdf.inputs['Specular IOR Level'].default_value = 0.6
bsdf.inputs['Coat Weight'].default_value = 0.3  # clearcoat for shine
bsdf.inputs['Coat Roughness'].default_value = 0.05

skirt.data.materials.append(mat_white)
body.data.materials.append(mat_white)
cap.data.materials.append(mat_white)
for ring in grip_rings:
    ring.data.materials.append(mat_white)

# Bold black indicator
mat_indicator = bpy.data.materials.new('BlackIndicator')
mat_indicator.use_nodes = True
bsdf_ind = mat_indicator.node_tree.nodes['Principled BSDF']
bsdf_ind.inputs['Base Color'].default_value = (0.02, 0.02, 0.02, 1.0)
bsdf_ind.inputs['Roughness'].default_value = 0.4

indicator.data.materials.append(mat_indicator)
dot.data.materials.append(mat_indicator)

# ============================================================
# Parent to pivot
# ============================================================
bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
pivot = bpy.context.active_object
pivot.name = 'KnobPivot'

for obj in [skirt, body, cap, indicator, dot] + grip_rings:
    obj.parent = pivot

# ============================================================
# Shadow catcher
# ============================================================
bpy.ops.mesh.primitive_plane_add(size=4, location=(0, 0, 0))
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
camera.data.ortho_scale = 1.15
camera.rotation_euler = (0, 0, 0)
scene.camera = camera

# ============================================================
# Lighting (studio 3-point + overhead)
# ============================================================

# Main key light (slightly right, slightly forward)
bpy.ops.object.light_add(type='AREA', location=(0.6, -0.4, 2.5))
key = bpy.context.active_object
key.data.energy = 40
key.data.size = 2.0
key.data.color = (1.0, 0.98, 0.95)  # slightly warm

# Fill light (left side)
bpy.ops.object.light_add(type='AREA', location=(-0.7, 0.3, 2.0))
fill = bpy.context.active_object
fill.data.energy = 20
fill.data.size = 2.0
fill.data.color = (0.95, 0.97, 1.0)  # slightly cool

# Overhead soft (directly above for dome highlight)
bpy.ops.object.light_add(type='AREA', location=(0, 0, 3.5))
overhead = bpy.context.active_object
overhead.data.energy = 25
overhead.data.size = 3.0

# Back rim light
bpy.ops.object.light_add(type='AREA', location=(0, 0.8, 1.5))
rim = bpy.context.active_object
rim.data.energy = 12
rim.data.size = 1.0

# ============================================================
# Render 128 frames
# ============================================================
for i in range(FRAMES):
    angle = math.radians(-135 + (i / (FRAMES - 1)) * 270)
    pivot.rotation_euler[2] = angle
    bpy.context.view_layer.update()
    scene.render.filepath = os.path.join(OUTPUT_DIR, f'frame_{i:04d}.png')
    bpy.ops.render.render(write_still=True)

print(f"DONE: Rendered {FRAMES} frames to {OUTPUT_DIR}")
