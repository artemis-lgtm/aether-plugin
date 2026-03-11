"""
Pedal v3: Photorealistic guitar pedal enclosure.
Key changes from v1/v2:
- Nishita sky texture for realistic environment lighting + metal reflections
- Much thicker enclosure with large bevel (visible edge ring from top-down)
- Powder-coat textured surface on edges (subtle orange-peel bump)
- Anodized sky-blue metal edges (matches artwork palette)
- Artwork printed on surface with clearcoat reflection
- Dark wood desk surface underneath for contact shadow + grounding
- Ambient occlusion + contact shadows for depth
- High-quality screws with actual geometry
"""

import bpy
import bmesh
import math
import os

OUTPUT_PATH = '/tmp/aether-art/pedal_v3.png'
ARTWORK_PATH = '/tmp/aether-art/background-original.png'

RENDER_W = 1020
RENDER_H = 620

# Pedal dimensions -- THICK for visible edges from top-down
PEDAL_W = 5.1
PEDAL_H = 3.1
PEDAL_D = 1.5   # extra thick to ensure edges are prominent in the render
BEVEL = 0.14    # tighter radius like real Hammond enclosures

bpy.ops.wm.read_factory_settings(use_empty=True)

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 200  # quality render
scene.render.resolution_x = RENDER_W
scene.render.resolution_y = RENDER_H
scene.render.film_transparent = False  # want desk/environment
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'

# Filmic tone mapping for better highlight recovery
scene.view_settings.view_transform = 'Filmic'
scene.view_settings.look = 'Medium Contrast'
scene.view_settings.exposure = -0.5  # slight underexpose to recover highlights

# ============================================================
# WORLD: Nishita sky for realistic outdoor/studio environment
# ============================================================
world = bpy.data.worlds.new('World')
scene.world = world
world.use_nodes = True
wn = world.node_tree.nodes
wl = world.node_tree.links
wn.clear()

# Studio HDRI for realistic metal reflections
env_tex = wn.new('ShaderNodeTexEnvironment')
env_tex.image = bpy.data.images.load('/tmp/aether-art/outdoor.hdr')
env_tex.interpolation = 'Smart'

bg = wn.new('ShaderNodeBackground')
bg.inputs['Strength'].default_value = 1.5  # balanced -- not overexposed

out_w = wn.new('ShaderNodeOutputWorld')
wl.new(env_tex.outputs['Color'], bg.inputs['Color'])
wl.new(bg.outputs['Background'], out_w.inputs['Surface'])

# ============================================================
# PEDAL ENCLOSURE
# ============================================================
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, PEDAL_D / 2))
pedal = bpy.context.active_object
pedal.name = 'Pedal'
pedal.scale = (PEDAL_W / 2, PEDAL_H / 2, PEDAL_D / 2)
bpy.ops.object.transform_apply(scale=True)

# Main bevel for rounded corners
bpy.ops.object.modifier_add(type='BEVEL')
pedal.modifiers['Bevel'].width = BEVEL
pedal.modifiers['Bevel'].segments = 4
pedal.modifiers['Bevel'].limit_method = 'ANGLE'
pedal.modifiers['Bevel'].angle_limit = math.radians(30)
bpy.ops.object.modifier_apply(modifier='Bevel')

# Sharp chamfer at top edge (creates bright highlight line)
bpy.ops.object.modifier_add(type='BEVEL')
pedal.modifiers['Bevel'].width = 0.02  # thin sharp chamfer
pedal.modifiers['Bevel'].segments = 1   # single face = sharp highlight
pedal.modifiers['Bevel'].limit_method = 'ANGLE'
pedal.modifiers['Bevel'].angle_limit = math.radians(60)  # only sharp edges
bpy.ops.object.modifier_apply(modifier='Bevel')

# Smooth shading on edges (critical for reflections)
bpy.ops.object.shade_smooth()

# Blender 5.0+: use Auto Smooth modifier instead of deprecated mesh attribute
bpy.ops.object.modifier_add(type='NODES')
mod = pedal.modifiers[-1]
mod.name = 'AutoSmooth'
# Use the built-in smooth by angle geometry nodes group
import importlib
try:
    bpy.ops.object.modifier_add(type='SMOOTH')
    pedal.modifiers['Smooth'].factor = 0.5
    pedal.modifiers['Smooth'].iterations = 1
except:
    pass
# Remove the nodes modifier we just added (it's empty)
try:
    bpy.ops.object.modifier_remove(modifier='AutoSmooth')
except:
    pass

# ============================================================
# TOP MATERIAL: Artwork with clearcoat (printed label on metal)
# ============================================================
mat_top = bpy.data.materials.new('ArtworkTop')
mat_top.use_nodes = True
tree = mat_top.node_tree
tree.nodes.clear()

out_m = tree.nodes.new('ShaderNodeOutputMaterial')
principled = tree.nodes.new('ShaderNodeBsdfPrincipled')

# Printed surface: ink on metal under clearcoat
principled.inputs['Roughness'].default_value = 0.2
principled.inputs['Specular IOR Level'].default_value = 0.5
principled.inputs['Coat Weight'].default_value = 0.3   # less glassy
principled.inputs['Coat Roughness'].default_value = 0.12  # more satin, less mirror
principled.inputs['Coat IOR'].default_value = 1.5

# Artwork texture
tex = tree.nodes.new('ShaderNodeTexImage')
tex.image = bpy.data.images.load(ARTWORK_PATH)

# Clearcoat roughness variation (orange peel micro-texture)
rough_noise = tree.nodes.new('ShaderNodeTexNoise')
rough_noise.inputs['Scale'].default_value = 400  # fine grain
rough_noise.inputs['Detail'].default_value = 10
rough_noise.inputs['Roughness'].default_value = 0.5

# Map noise to roughness variation (0.15 to 0.30 range)
rough_map = tree.nodes.new('ShaderNodeMapRange')
rough_map.inputs['From Min'].default_value = 0.0
rough_map.inputs['From Max'].default_value = 1.0
rough_map.inputs['To Min'].default_value = 0.15
rough_map.inputs['To Max'].default_value = 0.30

# Orange peel clearcoat bump
coat_bump_noise = tree.nodes.new('ShaderNodeTexNoise')
coat_bump_noise.inputs['Scale'].default_value = 250
coat_bump_noise.inputs['Detail'].default_value = 6
coat_bump_noise.inputs['Roughness'].default_value = 0.7

bump = tree.nodes.new('ShaderNodeBump')
bump.inputs['Strength'].default_value = 0.015  # very subtle orange peel
bump.inputs['Distance'].default_value = 0.003

tree.links.new(tex.outputs['Color'], principled.inputs['Base Color'])
tree.links.new(rough_noise.outputs['Fac'], rough_map.inputs['Value'])
tree.links.new(rough_map.outputs['Result'], principled.inputs['Roughness'])
tree.links.new(coat_bump_noise.outputs['Fac'], bump.inputs['Height'])
tree.links.new(bump.outputs['Normal'], principled.inputs['Normal'])
tree.links.new(principled.outputs['BSDF'], out_m.inputs['Surface'])

# ============================================================
# EDGE MATERIAL: Anodized sky-blue aluminum
# ============================================================
mat_edge = bpy.data.materials.new('AnodizedEdge')
mat_edge.use_nodes = True
e_tree = mat_edge.node_tree
e_tree.nodes.clear()

e_out = e_tree.nodes.new('ShaderNodeOutputMaterial')
e_bsdf = e_tree.nodes.new('ShaderNodeBsdfPrincipled')

# Simple sky-blue metallic -- same approach that worked in metal_test
# Key: sky blue as the metal color directly, high metallic, low roughness
e_bsdf.inputs['Base Color'].default_value = (0.35, 0.55, 0.80, 1.0)  # sky blue metal
e_bsdf.inputs['Metallic'].default_value = 1.0
e_bsdf.inputs['Roughness'].default_value = 0.15  # satin -- shows HDRI
e_tree.links.new(e_bsdf.outputs['BSDF'], e_out.inputs['Surface'])

# ============================================================
# BOTTOM MATERIAL
# ============================================================
mat_bottom = bpy.data.materials.new('Bottom')
mat_bottom.use_nodes = True
b_bsdf = mat_bottom.node_tree.nodes['Principled BSDF']
b_bsdf.inputs['Base Color'].default_value = (0.05, 0.05, 0.05, 1.0)
b_bsdf.inputs['Roughness'].default_value = 0.9

# ============================================================
# ASSIGN MATERIALS + UV
# ============================================================
pedal.data.materials.append(mat_top)     # 0
pedal.data.materials.append(mat_edge)    # 1
pedal.data.materials.append(mat_bottom)  # 2

bpy.context.view_layer.objects.active = pedal
bpy.ops.object.mode_set(mode='EDIT')
bm = bmesh.from_edit_mesh(pedal.data)
bm.faces.ensure_lookup_table()

for face in bm.faces:
    if face.normal.z > 0.95:
        face.material_index = 0  # top -> artwork (only truly flat top faces)
    elif face.normal.z < -0.5:
        face.material_index = 2  # bottom
    else:
        face.material_index = 1  # sides + ALL bevel transition faces -> anodized edge

# UV map for top face
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
# SCREWS (detailed Phillips head)
# ============================================================
mat_screw = bpy.data.materials.new('ScrewChrome')
mat_screw.use_nodes = True
sc_tree = mat_screw.node_tree
sc_tree.nodes.clear()
sc_out = sc_tree.nodes.new('ShaderNodeOutputMaterial')
sc_bsdf = sc_tree.nodes.new('ShaderNodeBsdfPrincipled')
sc_bsdf.inputs['Base Color'].default_value = (0.78, 0.80, 0.82, 1.0)
sc_bsdf.inputs['Metallic'].default_value = 0.95
sc_bsdf.inputs['Roughness'].default_value = 0.06
sc_bsdf.inputs['Coat Weight'].default_value = 0.2
sc_bsdf.inputs['Coat Roughness'].default_value = 0.02
sc_tree.links.new(sc_bsdf.outputs['BSDF'], sc_out.inputs['Surface'])

mat_slot = bpy.data.materials.new('ScrewSlot')
mat_slot.use_nodes = True
sl_bsdf = mat_slot.node_tree.nodes['Principled BSDF']
sl_bsdf.inputs['Base Color'].default_value = (0.03, 0.03, 0.03, 1.0)
sl_bsdf.inputs['Metallic'].default_value = 0.85
sl_bsdf.inputs['Roughness'].default_value = 0.5

screw_inset = 0.30
screw_positions = [
    (PEDAL_W/2 - screw_inset, PEDAL_H/2 - screw_inset * 0.7),
    (-PEDAL_W/2 + screw_inset, PEDAL_H/2 - screw_inset * 0.7),
    (PEDAL_W/2 - screw_inset, -PEDAL_H/2 + screw_inset * 0.7),
    (-PEDAL_W/2 + screw_inset, -PEDAL_H/2 + screw_inset * 0.7),
]

for idx, (sx, sy) in enumerate(screw_positions):
    # Screw recess (smaller, recessed into surface)
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.065, depth=0.03,
        location=(sx, sy, PEDAL_D - 0.015),
        vertices=32
    )
    recess = bpy.context.active_object
    recess.data.materials.append(mat_slot)
    
    # Screw head (smaller dome)
    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=0.055, segments=32, ring_count=16,
        location=(sx, sy, PEDAL_D + 0.005)
    )
    head = bpy.context.active_object
    head.scale[2] = 0.3
    bpy.ops.object.transform_apply(scale=True)
    head.data.materials.append(mat_screw)
    
    # Phillips cross (proportional to smaller screw)
    for angle in [0, math.pi/2]:
        bpy.ops.mesh.primitive_cube_add(size=1, location=(sx, sy, PEDAL_D + 0.018))
        cross = bpy.context.active_object
        cross.scale = (0.004, 0.038, 0.008)
        cross.rotation_euler[2] = angle
        bpy.ops.object.transform_apply(scale=True, rotation=True)
        cross.data.materials.append(mat_slot)

# ============================================================
# LED with proper emission
# ============================================================
led_y = PEDAL_H/2 - 0.22

# LED housing (chrome ring)
bpy.ops.mesh.primitive_torus_add(
    major_radius=0.07, minor_radius=0.015,
    location=(0, led_y, PEDAL_D + 0.01),
    major_segments=32, minor_segments=12
)
led_ring = bpy.context.active_object
led_ring.data.materials.append(mat_screw)

# LED dome (translucent red)
bpy.ops.mesh.primitive_uv_sphere_add(
    radius=0.055, segments=24, ring_count=12,
    location=(0, led_y, PEDAL_D + 0.025)
)
led = bpy.context.active_object
led.scale[2] = 0.4
bpy.ops.object.transform_apply(scale=True)

mat_led = bpy.data.materials.new('LEDRed')
mat_led.use_nodes = True
led_tree = mat_led.node_tree
led_tree.nodes.clear()
led_out = led_tree.nodes.new('ShaderNodeOutputMaterial')
led_bsdf = led_tree.nodes.new('ShaderNodeBsdfPrincipled')
led_bsdf.inputs['Base Color'].default_value = (1.0, 0.02, 0.01, 1.0)
led_bsdf.inputs['Emission Color'].default_value = (1.0, 0.05, 0.01, 1.0)
led_bsdf.inputs['Emission Strength'].default_value = 25.0
led_bsdf.inputs['Roughness'].default_value = 0.05
led_bsdf.inputs['Transmission Weight'].default_value = 0.3  # translucent dome
led_tree.links.new(led_bsdf.outputs['BSDF'], led_out.inputs['Surface'])
led.data.materials.append(mat_led)

# ============================================================
# DESK SURFACE (dark wood)
# ============================================================
bpy.ops.mesh.primitive_plane_add(size=15, location=(0, 0, -0.01))
desk = bpy.context.active_object
desk.name = 'Desk'

mat_desk = bpy.data.materials.new('DarkWood')
mat_desk.use_nodes = True
d_tree = mat_desk.node_tree
d_tree.nodes.clear()
d_out = d_tree.nodes.new('ShaderNodeOutputMaterial')
d_bsdf = d_tree.nodes.new('ShaderNodeBsdfPrincipled')
d_bsdf.inputs['Base Color'].default_value = (0.06, 0.04, 0.03, 1.0)  # very dark wood
d_bsdf.inputs['Roughness'].default_value = 0.55
d_bsdf.inputs['Specular IOR Level'].default_value = 0.3

# Directional wood grain using wave + noise
d_coord = d_tree.nodes.new('ShaderNodeTexCoord')
d_mapping = d_tree.nodes.new('ShaderNodeMapping')
d_mapping.inputs['Scale'].default_value = (8.0, 1.0, 1.0)  # stretch along one axis

d_wave = d_tree.nodes.new('ShaderNodeTexWave')
d_wave.wave_type = 'BANDS'
d_wave.bands_direction = 'X'
d_wave.inputs['Scale'].default_value = 5.0
d_wave.inputs['Distortion'].default_value = 4.0
d_wave.inputs['Detail'].default_value = 3.0
d_wave.inputs['Detail Scale'].default_value = 1.5

d_noise = d_tree.nodes.new('ShaderNodeTexNoise')
d_noise.inputs['Scale'].default_value = 50
d_noise.inputs['Detail'].default_value = 8
d_noise.inputs['Roughness'].default_value = 0.6

# Combine wave + noise for wood pattern
d_mix_fac = d_tree.nodes.new('ShaderNodeMix')
d_mix_fac.data_type = 'FLOAT'
d_mix_fac.inputs['Factor'].default_value = 0.4

d_ramp = d_tree.nodes.new('ShaderNodeValToRGB')
d_ramp.color_ramp.elements[0].position = 0.25
d_ramp.color_ramp.elements[0].color = (0.03, 0.018, 0.012, 1.0)  # very dark walnut
d_ramp.color_ramp.elements[1].position = 0.65
d_ramp.color_ramp.elements[1].color = (0.12, 0.08, 0.055, 1.0)  # medium grain -- more contrast

# Roughness variation for wood
d_rough_map = d_tree.nodes.new('ShaderNodeMapRange')
d_rough_map.inputs['To Min'].default_value = 0.4
d_rough_map.inputs['To Max'].default_value = 0.65

d_tree.links.new(d_coord.outputs['Object'], d_mapping.inputs['Vector'])
d_tree.links.new(d_mapping.outputs['Vector'], d_wave.inputs['Vector'])
d_tree.links.new(d_mapping.outputs['Vector'], d_noise.inputs['Vector'])
d_tree.links.new(d_wave.outputs['Fac'], d_mix_fac.inputs[2])
d_tree.links.new(d_noise.outputs['Fac'], d_mix_fac.inputs[3])
d_tree.links.new(d_mix_fac.outputs[0], d_ramp.inputs['Fac'])
d_tree.links.new(d_ramp.outputs['Color'], d_bsdf.inputs['Base Color'])
d_tree.links.new(d_wave.outputs['Fac'], d_rough_map.inputs['Value'])
d_tree.links.new(d_rough_map.outputs['Result'], d_bsdf.inputs['Roughness'])
d_tree.links.new(d_bsdf.outputs['BSDF'], d_out.inputs['Surface'])
desk.data.materials.append(mat_desk)

# ============================================================
# CONTACT SHADOW: thin dark plane right under pedal
# ============================================================
# This creates a tighter ambient occlusion effect at the base
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0.005))
shadow_plane = bpy.context.active_object
shadow_plane.name = 'ContactShadow'
shadow_plane.scale = (PEDAL_W/2 + 0.02, PEDAL_H/2 + 0.02, 1)
bpy.ops.object.transform_apply(scale=True)

mat_shadow = bpy.data.materials.new('ContactShadow')
mat_shadow.use_nodes = True
mat_shadow.blend_method = 'BLEND' if hasattr(mat_shadow, 'blend_method') else None
sh_bsdf = mat_shadow.node_tree.nodes['Principled BSDF']
sh_bsdf.inputs['Base Color'].default_value = (0.0, 0.0, 0.0, 1.0)
sh_bsdf.inputs['Roughness'].default_value = 1.0
sh_bsdf.inputs['Alpha'].default_value = 0.5
shadow_plane.data.materials.append(mat_shadow)

# ============================================================
# CAMERA: Top-down, framed tight on pedal with small desk border
# ============================================================
# Perspective camera: 50mm, 20 degrees from vertical
# This WILL show the front edge of the pedal
from mathutils import Vector

# Hero angle: 30 degrees from vertical, slight Y rotation for 3/4 view
cam_tilt_deg = 30
cam_yaw_deg = 8  # slight rotation to show two side edges
cam_dist = 5.5

cam_x = cam_dist * math.sin(math.radians(cam_yaw_deg)) * math.sin(math.radians(cam_tilt_deg))
cam_y = -cam_dist * math.cos(math.radians(cam_yaw_deg)) * math.sin(math.radians(cam_tilt_deg))
cam_z = cam_dist * math.cos(math.radians(cam_tilt_deg))

bpy.ops.object.camera_add(location=(cam_x, cam_y, cam_z))
camera = bpy.context.active_object
camera.data.type = 'PERSP'
camera.data.lens = 65  # moderate telephoto, some perspective but controlled
camera.data.clip_start = 0.01
camera.data.clip_end = 200.0

# Point camera at center of pedal
target = Vector((0, 0, PEDAL_D / 2))
direction = target - camera.location
rot = direction.to_track_quat('-Z', 'Y')
camera.rotation_euler = rot.to_euler()
scene.camera = camera

# ============================================================
# LIGHTING: Multi-point studio setup
# ============================================================

# LIGHTING: HDRI does ambient + reflections, only 2 accent lights
# Key light (right, low angle to catch edge chamfers)
bpy.ops.object.light_add(type='AREA', location=(3.5, -1.5, 2.0))
key = bpy.context.active_object
key.name = 'Key'
key.data.energy = 40
key.data.size = 1.5  # smaller = sharper specular on metal
key.rotation_euler = (math.radians(35), math.radians(-30), 0)

# Rim backlight (edge separation)
bpy.ops.object.light_add(type='AREA', location=(-1.5, 2.5, 1.0))
rim = bpy.context.active_object
rim.name = 'Rim'
rim.data.energy = 60
rim.data.size = 1.0
rim.rotation_euler = (math.radians(40), math.radians(20), 0)

# Front edge light -- specifically aimed at the front face of the enclosure
bpy.ops.object.light_add(type='AREA', location=(0, -3.0, 0.5))
front_edge = bpy.context.active_object
front_edge.name = 'FrontEdge'
front_edge.data.energy = 60  # moderate
front_edge.data.size = 3.0
front_edge.rotation_euler = (math.radians(80), 0, 0)  # pointing almost straight at front face

# Right side edge light
bpy.ops.object.light_add(type='AREA', location=(4.0, 0, 0.5))
side_edge = bpy.context.active_object
side_edge.name = 'SideEdge'
side_edge.data.energy = 80
side_edge.data.size = 2.0
side_edge.rotation_euler = (math.radians(80), math.radians(-80), 0)

# ============================================================
# RENDER
# ============================================================
scene.render.filepath = OUTPUT_PATH
bpy.ops.render.render(write_still=True)
print(f"DONE: Pedal v3 rendered to {OUTPUT_PATH}")
