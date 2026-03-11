"""
Blender script: Render a photorealistic guitar pedal enclosure with crayon artwork texture.
The existing background.png is UV-mapped onto the top face of a 3D metal box.
Orthographic top-down render for VST plugin background.
"""

import bpy
import bmesh
import math
import os

OUTPUT_PATH = '/tmp/aether-art/pedal_background.png'
ARTWORK_PATH = '/Users/artemis/.openclaw/workspace/projects/aether/resources/background.png'

# Target aspect ratio: 1020x620 (current plugin window)
RENDER_W = 1020
RENDER_H = 620

# Pedal proportions (in Blender units, matching aspect ratio)
PEDAL_W = 5.1   # width
PEDAL_H = 3.1   # depth (front-to-back)
PEDAL_D = 0.4   # thickness/height of the enclosure
BEVEL = 0.08    # edge bevel radius
SCREW_RADIUS = 0.06

bpy.ops.wm.read_factory_settings(use_empty=True)

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 128
scene.render.resolution_x = RENDER_W
scene.render.resolution_y = RENDER_H
scene.render.film_transparent = False  # we want a background here
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'

# ============================================================
# WORLD - dark studio floor / workspace feel
# ============================================================
world = bpy.data.worlds.new('World')
scene.world = world
world.use_nodes = True
wn = world.node_tree.nodes
wl = world.node_tree.links
wn.clear()
bg = wn.new('ShaderNodeBackground')
bg.inputs['Strength'].default_value = 0.3
bg.inputs['Color'].default_value = (0.15, 0.15, 0.18, 1.0)  # dark studio
output_w = wn.new('ShaderNodeOutputWorld')
wl.new(bg.outputs['Background'], output_w.inputs['Surface'])

# ============================================================
# PEDAL ENCLOSURE - rounded rectangle box
# ============================================================
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, PEDAL_D / 2))
pedal = bpy.context.active_object
pedal.name = 'PedalEnclosure'
pedal.scale = (PEDAL_W / 2, PEDAL_H / 2, PEDAL_D / 2)
bpy.ops.object.transform_apply(scale=True)

# Bevel all edges for that smooth metal enclosure feel
bpy.ops.object.modifier_add(type='BEVEL')
pedal.modifiers['Bevel'].width = BEVEL
pedal.modifiers['Bevel'].segments = 4
pedal.modifiers['Bevel'].limit_method = 'ANGLE'
pedal.modifiers['Bevel'].angle_limit = math.radians(30)
bpy.ops.object.modifier_apply(modifier='Bevel')

# ============================================================
# UV UNWRAP top face and apply artwork texture
# ============================================================
# Create material with the artwork texture
mat_top = bpy.data.materials.new('PedalTop')
mat_top.use_nodes = True
tree = mat_top.node_tree
nodes = tree.nodes
links = tree.links
nodes.clear()

out_mat = nodes.new('ShaderNodeOutputMaterial')
principled = nodes.new('ShaderNodeBsdfPrincipled')
principled.inputs['Roughness'].default_value = 0.35  # slightly rough painted surface
principled.inputs['Specular IOR Level'].default_value = 0.3
principled.inputs['Coat Weight'].default_value = 0.15  # subtle clearcoat over the paint

# Load artwork texture
tex_node = nodes.new('ShaderNodeTexImage')
artwork_img = bpy.data.images.load(ARTWORK_PATH)
tex_node.image = artwork_img

# Add subtle bump from the texture (crayon texture feel)
bump_node = nodes.new('ShaderNodeBump')
bump_node.inputs['Strength'].default_value = 0.05  # very subtle
bump_node.inputs['Distance'].default_value = 0.01

links.new(tex_node.outputs['Color'], principled.inputs['Base Color'])
links.new(tex_node.outputs['Color'], bump_node.inputs['Height'])
links.new(bump_node.outputs['Normal'], principled.inputs['Normal'])
links.new(principled.outputs['BSDF'], out_mat.inputs['Surface'])

# Metal side material (for the enclosure sides/edges)
mat_metal = bpy.data.materials.new('PedalMetal')
mat_metal.use_nodes = True
m_nodes = mat_metal.node_tree.nodes
m_links = mat_metal.node_tree.links
bsdf_m = m_nodes['Principled BSDF']
bsdf_m.inputs['Base Color'].default_value = (0.6, 0.62, 0.65, 1.0)  # brushed aluminum
bsdf_m.inputs['Metallic'].default_value = 0.85
bsdf_m.inputs['Roughness'].default_value = 0.25
bsdf_m.inputs['Specular IOR Level'].default_value = 0.5

# Assign materials: top face gets artwork, sides get metal
pedal.data.materials.append(mat_top)    # slot 0
pedal.data.materials.append(mat_metal)  # slot 1

# Go into edit mode to assign materials by face normal
bpy.context.view_layer.objects.active = pedal
bpy.ops.object.mode_set(mode='EDIT')
bm = bmesh.from_edit_mesh(pedal.data)
bm.faces.ensure_lookup_table()

for face in bm.faces:
    # Top face: normal pointing up (z > 0.9)
    if face.normal.z > 0.9:
        face.material_index = 0  # artwork
    else:
        face.material_index = 1  # metal

# Manual UV assignment for top face - map to fill entire texture
uv_layer = bm.loops.layers.uv.verify()
for face in bm.faces:
    if face.normal.z > 0.9:
        # Find bounds of this face to map UV 0-1
        xs = [v.co.x for v in face.verts]
        ys = [v.co.y for v in face.verts]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        range_x = max_x - min_x if max_x != min_x else 1
        range_y = max_y - min_y if max_y != min_y else 1
        for loop in face.loops:
            u = (loop.vert.co.x - min_x) / range_x
            v = (loop.vert.co.y - min_y) / range_y
            loop[uv_layer].uv = (u, v)

bmesh.update_edit_mesh(pedal.data)
bpy.ops.object.mode_set(mode='OBJECT')

# ============================================================
# SCREWS (4 corners)
# ============================================================
screw_positions = [
    (PEDAL_W/2 - 0.25, PEDAL_H/2 - 0.2),
    (-PEDAL_W/2 + 0.25, PEDAL_H/2 - 0.2),
    (PEDAL_W/2 - 0.25, -PEDAL_H/2 + 0.2),
    (-PEDAL_W/2 + 0.25, -PEDAL_H/2 + 0.2),
]

mat_screw = bpy.data.materials.new('ScrewMetal')
mat_screw.use_nodes = True
s_bsdf = mat_screw.node_tree.nodes['Principled BSDF']
s_bsdf.inputs['Base Color'].default_value = (0.5, 0.5, 0.52, 1.0)
s_bsdf.inputs['Metallic'].default_value = 0.95
s_bsdf.inputs['Roughness'].default_value = 0.15

for idx, (sx, sy) in enumerate(screw_positions):
    # Screw head (cylinder)
    bpy.ops.mesh.primitive_cylinder_add(
        radius=SCREW_RADIUS, depth=0.03,
        location=(sx, sy, PEDAL_D + 0.015),
        vertices=32
    )
    screw = bpy.context.active_object
    screw.name = f'Screw_{idx}'
    screw.data.materials.append(mat_screw)
    
    # Phillips cross on screw (two thin cubes)
    for angle in [0, math.pi/2]:
        bpy.ops.mesh.primitive_cube_add(
            size=1,
            location=(sx, sy, PEDAL_D + 0.032)
        )
        cross = bpy.context.active_object
        cross.scale = (0.004, SCREW_RADIUS * 0.7, 0.003)
        cross.rotation_euler[2] = angle
        bpy.ops.object.transform_apply(scale=True, rotation=True)
        
        mat_cross = bpy.data.materials.new(f'CrossSlot_{idx}_{angle}')
        mat_cross.use_nodes = True
        c_bsdf = mat_cross.node_tree.nodes['Principled BSDF']
        c_bsdf.inputs['Base Color'].default_value = (0.15, 0.15, 0.15, 1.0)
        c_bsdf.inputs['Metallic'].default_value = 0.9
        c_bsdf.inputs['Roughness'].default_value = 0.4
        cross.data.materials.append(mat_cross)

# ============================================================
# LED indicator (small, red, glowing)
# ============================================================
bpy.ops.mesh.primitive_cylinder_add(
    radius=0.04, depth=0.03,
    location=(0, PEDAL_H/2 - 0.15, PEDAL_D + 0.015),
    vertices=32
)
led = bpy.context.active_object
led.name = 'LED'

mat_led = bpy.data.materials.new('LEDGlow')
mat_led.use_nodes = True
led_tree = mat_led.node_tree
led_nodes = led_tree.nodes
led_links = led_tree.links
led_nodes.clear()
led_out = led_nodes.new('ShaderNodeOutputMaterial')
led_bsdf = led_nodes.new('ShaderNodeBsdfPrincipled')
led_bsdf.inputs['Base Color'].default_value = (1.0, 0.1, 0.05, 1.0)
led_bsdf.inputs['Emission Color'].default_value = (1.0, 0.15, 0.05, 1.0)
led_bsdf.inputs['Emission Strength'].default_value = 8.0
led_bsdf.inputs['Roughness'].default_value = 0.1
led_links.new(led_bsdf.outputs['BSDF'], led_out.inputs['Surface'])
led.data.materials.append(mat_led)

# LED bezel ring
bpy.ops.mesh.primitive_torus_add(
    major_radius=0.05, minor_radius=0.01,
    location=(0, PEDAL_H/2 - 0.15, PEDAL_D + 0.01),
    major_segments=32, minor_segments=8
)
led_bezel = bpy.context.active_object
led_bezel.name = 'LEDBezel'
led_bezel.data.materials.append(mat_screw)

# ============================================================
# Surface beneath pedal (dark wood/desk)
# ============================================================
bpy.ops.mesh.primitive_plane_add(size=12, location=(0, 0, -0.01))
desk = bpy.context.active_object
desk.name = 'Desk'

mat_desk = bpy.data.materials.new('DarkDesk')
mat_desk.use_nodes = True
d_bsdf = mat_desk.node_tree.nodes['Principled BSDF']
d_bsdf.inputs['Base Color'].default_value = (0.08, 0.07, 0.06, 1.0)
d_bsdf.inputs['Roughness'].default_value = 0.7
desk.data.materials.append(mat_desk)

# ============================================================
# Camera (orthographic, straight down, framing the pedal)
# ============================================================
bpy.ops.object.camera_add(location=(0, 0, 6))
camera = bpy.context.active_object
camera.name = 'TopCam'
camera.data.type = 'ORTHO'
# Scale to frame the pedal with a small margin
camera.data.ortho_scale = max(PEDAL_W, PEDAL_H * (RENDER_W / RENDER_H)) * 1.05
camera.rotation_euler = (0, 0, 0)
scene.camera = camera

# ============================================================
# LIGHTING
# ============================================================
# Large overhead softbox
bpy.ops.object.light_add(type='AREA', location=(0, 0, 5))
overhead = bpy.context.active_object
overhead.data.energy = 100
overhead.data.size = 4.0
overhead.data.color = (1.0, 0.98, 0.96)

# Key light (right)
bpy.ops.object.light_add(type='AREA', location=(2.5, -1.0, 3.5))
key = bpy.context.active_object
key.data.energy = 60
key.data.size = 2.0
key.rotation_euler = (math.radians(20), math.radians(-15), 0)

# Fill (left)
bpy.ops.object.light_add(type='AREA', location=(-2.0, 0.5, 3.0))
fill = bpy.context.active_object
fill.data.energy = 30
fill.data.size = 2.0

# Back rim (for edge definition on metal)
bpy.ops.object.light_add(type='AREA', location=(0, 2.0, 2.0))
rim = bpy.context.active_object
rim.data.energy = 25
rim.data.size = 1.5

# ============================================================
# RENDER
# ============================================================
scene.render.filepath = OUTPUT_PATH
bpy.ops.render.render(write_still=True)
print(f"DONE: Pedal rendered to {OUTPUT_PATH}")
