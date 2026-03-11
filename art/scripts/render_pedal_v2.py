"""
Pedal v2: Fill the frame, bright lighting, real screws, LED glow, transparent background
The pedal IS the plugin window -- no desk/void around it
"""

import bpy
import bmesh
import math
import os

OUTPUT_PATH = '/tmp/aether-art/pedal_v2.png'
ARTWORK_PATH = '/Users/artemis/.openclaw/workspace/projects/aether/resources/background.png'

RENDER_W = 1020
RENDER_H = 620

# Pedal fills the entire frame with tiny margin
PEDAL_W = 5.1
PEDAL_H = 3.1
PEDAL_D = 0.5  # thicker for more visible edges
BEVEL = 0.12   # bigger bevel for visible rounded edges

bpy.ops.wm.read_factory_settings(use_empty=True)

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 96
scene.render.resolution_x = RENDER_W
scene.render.resolution_y = RENDER_H
scene.render.film_transparent = True  # transparent bg - pedal IS the UI
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'

# Compositor for LED bloom will be set up after scene is fully configured

# World - subtle warm ambient
world = bpy.data.worlds.new('World')
scene.world = world
world.use_nodes = True
wn = world.node_tree.nodes
wl = world.node_tree.links
wn.clear()
bg = wn.new('ShaderNodeBackground')
bg.inputs['Strength'].default_value = 1.0
bg.inputs['Color'].default_value = (0.85, 0.83, 0.80, 1.0)
out_w = wn.new('ShaderNodeOutputWorld')
wl.new(bg.outputs['Background'], out_w.inputs['Surface'])

# ============================================================
# PEDAL ENCLOSURE
# ============================================================
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, PEDAL_D / 2))
pedal = bpy.context.active_object
pedal.name = 'Pedal'
pedal.scale = (PEDAL_W / 2, PEDAL_H / 2, PEDAL_D / 2)
bpy.ops.object.transform_apply(scale=True)

bpy.ops.object.modifier_add(type='BEVEL')
pedal.modifiers['Bevel'].width = BEVEL
pedal.modifiers['Bevel'].segments = 5
pedal.modifiers['Bevel'].limit_method = 'ANGLE'
pedal.modifiers['Bevel'].angle_limit = math.radians(30)
bpy.ops.object.modifier_apply(modifier='Bevel')

# ============================================================
# MATERIALS
# ============================================================

# Top face - artwork texture
mat_top = bpy.data.materials.new('ArtworkTop')
mat_top.use_nodes = True
tree = mat_top.node_tree
tree.nodes.clear()
out_m = tree.nodes.new('ShaderNodeOutputMaterial')
principled = tree.nodes.new('ShaderNodeBsdfPrincipled')
principled.inputs['Roughness'].default_value = 0.3
principled.inputs['Specular IOR Level'].default_value = 0.4
principled.inputs['Coat Weight'].default_value = 0.2
principled.inputs['Coat Roughness'].default_value = 0.1

tex = tree.nodes.new('ShaderNodeTexImage')
tex.image = bpy.data.images.load(ARTWORK_PATH)

# Subtle bump from artwork
bump = tree.nodes.new('ShaderNodeBump')
bump.inputs['Strength'].default_value = 0.03
tree.links.new(tex.outputs['Color'], principled.inputs['Base Color'])
tree.links.new(tex.outputs['Color'], bump.inputs['Height'])
tree.links.new(bump.outputs['Normal'], principled.inputs['Normal'])
tree.links.new(principled.outputs['BSDF'], out_m.inputs['Surface'])

# Side/edge - powder-coated metal (sky blue to match the artwork)
mat_side = bpy.data.materials.new('PowderCoatSide')
mat_side.use_nodes = True
s_tree = mat_side.node_tree
s_bsdf = s_tree.nodes['Principled BSDF']
s_bsdf.inputs['Base Color'].default_value = (0.35, 0.55, 0.75, 1.0)  # sky blue metal
s_bsdf.inputs['Metallic'].default_value = 0.6
s_bsdf.inputs['Roughness'].default_value = 0.35
s_bsdf.inputs['Specular IOR Level'].default_value = 0.5

# Bottom face - dark
mat_bottom = bpy.data.materials.new('Bottom')
mat_bottom.use_nodes = True
b_bsdf = mat_bottom.node_tree.nodes['Principled BSDF']
b_bsdf.inputs['Base Color'].default_value = (0.1, 0.1, 0.1, 1.0)
b_bsdf.inputs['Roughness'].default_value = 0.8

# Assign materials
pedal.data.materials.append(mat_top)     # 0
pedal.data.materials.append(mat_side)    # 1
pedal.data.materials.append(mat_bottom)  # 2

bpy.context.view_layer.objects.active = pedal
bpy.ops.object.mode_set(mode='EDIT')
bm = bmesh.from_edit_mesh(pedal.data)
bm.faces.ensure_lookup_table()

for face in bm.faces:
    if face.normal.z > 0.5:
        face.material_index = 0
    elif face.normal.z < -0.5:
        face.material_index = 2
    else:
        face.material_index = 1

# UV for top face
uv_layer = bm.loops.layers.uv.verify()
top_faces = [f for f in bm.faces if f.normal.z > 0.5]
if top_faces:
    all_verts = []
    for f in top_faces:
        all_verts.extend([v.co for v in f.verts])
    min_x = min(v.x for v in all_verts)
    max_x = max(v.x for v in all_verts)
    min_y = min(v.y for v in all_verts)
    max_y = max(v.y for v in all_verts)
    range_x = max_x - min_x if max_x != min_x else 1
    range_y = max_y - min_y if max_y != min_y else 1
    
    for face in top_faces:
        for loop in face.loops:
            u = (loop.vert.co.x - min_x) / range_x
            v = (loop.vert.co.y - min_y) / range_y
            loop[uv_layer].uv = (u, v)

bmesh.update_edit_mesh(pedal.data)
bpy.ops.object.mode_set(mode='OBJECT')

# ============================================================
# SCREWS with Phillips heads
# ============================================================
mat_screw = bpy.data.materials.new('ScrewChrome')
mat_screw.use_nodes = True
sc = mat_screw.node_tree.nodes['Principled BSDF']
sc.inputs['Base Color'].default_value = (0.7, 0.72, 0.75, 1.0)
sc.inputs['Metallic'].default_value = 0.95
sc.inputs['Roughness'].default_value = 0.1

mat_slot = bpy.data.materials.new('ScrewSlot')
mat_slot.use_nodes = True
sl = mat_slot.node_tree.nodes['Principled BSDF']
sl.inputs['Base Color'].default_value = (0.08, 0.08, 0.08, 1.0)
sl.inputs['Metallic'].default_value = 0.9
sl.inputs['Roughness'].default_value = 0.5

screw_positions = [
    (PEDAL_W/2 - 0.3, PEDAL_H/2 - 0.22),
    (-PEDAL_W/2 + 0.3, PEDAL_H/2 - 0.22),
    (PEDAL_W/2 - 0.3, -PEDAL_H/2 + 0.22),
    (-PEDAL_W/2 + 0.3, -PEDAL_H/2 + 0.22),
]

for idx, (sx, sy) in enumerate(screw_positions):
    # Screw head - slightly domed
    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=0.07, location=(sx, sy, PEDAL_D + 0.02),
        segments=24, ring_count=12
    )
    screw = bpy.context.active_object
    screw.name = f'Screw_{idx}'
    screw.scale[2] = 0.35  # flatten to dome
    bpy.ops.object.transform_apply(scale=True)
    screw.data.materials.append(mat_screw)
    
    # Screw recess ring
    bpy.ops.mesh.primitive_torus_add(
        major_radius=0.075, minor_radius=0.008,
        location=(sx, sy, PEDAL_D + 0.005),
        major_segments=24, minor_segments=8
    )
    recess = bpy.context.active_object
    recess.data.materials.append(mat_slot)
    
    # Phillips cross slots
    for angle in [0, math.pi/2]:
        bpy.ops.mesh.primitive_cube_add(size=1, location=(sx, sy, PEDAL_D + 0.035))
        cross = bpy.context.active_object
        cross.scale = (0.005, 0.05, 0.008)
        cross.rotation_euler[2] = angle
        bpy.ops.object.transform_apply(scale=True, rotation=True)
        cross.data.materials.append(mat_slot)

# ============================================================
# LED with proper glow
# ============================================================
led_y = PEDAL_H/2 - 0.18

# LED lens (translucent dome)
bpy.ops.mesh.primitive_uv_sphere_add(
    radius=0.05, location=(0, led_y, PEDAL_D + 0.02),
    segments=24, ring_count=12
)
led = bpy.context.active_object
led.name = 'LED'
led.scale[2] = 0.5
bpy.ops.object.transform_apply(scale=True)

mat_led = bpy.data.materials.new('LEDRed')
mat_led.use_nodes = True
lt = mat_led.node_tree
lt.nodes.clear()
lo = lt.nodes.new('ShaderNodeOutputMaterial')
lb = lt.nodes.new('ShaderNodeBsdfPrincipled')
lb.inputs['Base Color'].default_value = (1.0, 0.05, 0.02, 1.0)
lb.inputs['Emission Color'].default_value = (1.0, 0.1, 0.02, 1.0)
lb.inputs['Emission Strength'].default_value = 15.0
lb.inputs['Roughness'].default_value = 0.1
lb.inputs['Alpha'].default_value = 0.9
lt.links.new(lb.outputs['BSDF'], lo.inputs['Surface'])
led.data.materials.append(mat_led)

# LED chrome bezel
bpy.ops.mesh.primitive_torus_add(
    major_radius=0.06, minor_radius=0.012,
    location=(0, led_y, PEDAL_D + 0.008),
    major_segments=32, minor_segments=8
)
bezel = bpy.context.active_object
bezel.data.materials.append(mat_screw)

# ============================================================
# Camera - tight crop, pedal fills frame
# ============================================================
bpy.ops.object.camera_add(location=(0, 0, 6))
camera = bpy.context.active_object
camera.data.type = 'ORTHO'
# Calculate ortho scale to fill frame with small margin
aspect = RENDER_W / RENDER_H
pedal_aspect = PEDAL_W / PEDAL_H
if pedal_aspect > aspect:
    camera.data.ortho_scale = PEDAL_W * 1.04  # width-limited
else:
    camera.data.ortho_scale = PEDAL_H * aspect * 1.04  # height-limited
camera.rotation_euler = (0, 0, 0)
scene.camera = camera

# ============================================================
# LIGHTING - bright studio
# ============================================================
# Large overhead softbox (main)
bpy.ops.object.light_add(type='AREA', location=(0, 0, 5))
o = bpy.context.active_object; o.data.energy = 120; o.data.size = 5.0

# Key (right, slightly angled for specular on edges)
bpy.ops.object.light_add(type='AREA', location=(3.0, -1.5, 3.5))
k = bpy.context.active_object; k.data.energy = 80; k.data.size = 2.5
k.rotation_euler = (math.radians(25), math.radians(-20), 0)

# Fill (left)
bpy.ops.object.light_add(type='AREA', location=(-2.5, 1.0, 3.0))
f = bpy.context.active_object; f.data.energy = 40; f.data.size = 2.0

# Edge lights (for metal rim definition)
bpy.ops.object.light_add(type='AREA', location=(0, 2.5, 1.5))
r1 = bpy.context.active_object; r1.data.energy = 30; r1.data.size = 1.5

bpy.ops.object.light_add(type='AREA', location=(0, -2.5, 1.5))
r2 = bpy.context.active_object; r2.data.energy = 30; r2.data.size = 1.5

# Skip compositor glare for now - just render clean

# ============================================================
# RENDER
# ============================================================
scene.render.filepath = OUTPUT_PATH
bpy.ops.render.render(write_still=True)
print(f"DONE: Pedal v2 rendered to {OUTPUT_PATH}")
