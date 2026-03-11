"""
Render individual hardware elements at high quality:
1. A single Phillips screw head (transparent bg)
2. A glowing LED (transparent bg)  
3. A metallic edge/border frame piece (transparent bg)
These get composited onto the 2D background artwork in Python.
"""

import bpy
import math
import os

OUTPUT_DIR = '/tmp/aether-art/hardware'
os.makedirs(OUTPUT_DIR, exist_ok=True)

def setup_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 128
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    
    world = bpy.data.worlds.new('World')
    scene.world = world
    world.use_nodes = True
    wn = world.node_tree.nodes
    wl = world.node_tree.links
    wn.clear()
    bg = wn.new('ShaderNodeBackground')
    bg.inputs['Strength'].default_value = 2.0
    bg.inputs['Color'].default_value = (0.9, 0.88, 0.86, 1.0)
    out = wn.new('ShaderNodeOutputWorld')
    wl.new(bg.outputs['Background'], out.inputs['Surface'])
    return scene

# ============================================================
# 1. PHILLIPS SCREW HEAD
# ============================================================
scene = setup_scene()
scene.render.resolution_x = 128
scene.render.resolution_y = 128

# Chrome material
mat_chrome = bpy.data.materials.new('Chrome')
mat_chrome.use_nodes = True
tree = mat_chrome.node_tree
tree.nodes.clear()
out_m = tree.nodes.new('ShaderNodeOutputMaterial')
bsdf = tree.nodes.new('ShaderNodeBsdfPrincipled')
bsdf.inputs['Base Color'].default_value = (0.75, 0.76, 0.78, 1.0)
bsdf.inputs['Metallic'].default_value = 0.95
bsdf.inputs['Roughness'].default_value = 0.08
bsdf.inputs['Coat Weight'].default_value = 0.3
bsdf.inputs['Coat Roughness'].default_value = 0.02
tree.links.new(bsdf.outputs['BSDF'], out_m.inputs['Surface'])

# Dark slot material
mat_slot = bpy.data.materials.new('Slot')
mat_slot.use_nodes = True
sl = mat_slot.node_tree.nodes['Principled BSDF']
sl.inputs['Base Color'].default_value = (0.05, 0.05, 0.05, 1.0)
sl.inputs['Metallic'].default_value = 0.8
sl.inputs['Roughness'].default_value = 0.6

# Screw head - dome shape
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.4, segments=48, ring_count=24, location=(0,0,0.1))
head = bpy.context.active_object
head.scale[2] = 0.3
bpy.ops.object.transform_apply(scale=True)
head.data.materials.append(mat_chrome)

# Outer rim/bevel ring
bpy.ops.mesh.primitive_torus_add(
    major_radius=0.42, minor_radius=0.04,
    location=(0, 0, 0.0), major_segments=48, minor_segments=12
)
rim = bpy.context.active_object
rim.data.materials.append(mat_chrome)

# Phillips cross
for angle in [0, math.pi/2]:
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.15))
    cross = bpy.context.active_object
    cross.scale = (0.02, 0.25, 0.03)
    cross.rotation_euler[2] = angle
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    cross.data.materials.append(mat_slot)

# Shadow catcher
bpy.ops.mesh.primitive_plane_add(size=3, location=(0, 0, -0.04))
sp = bpy.context.active_object
sp.is_shadow_catcher = True

# Camera
bpy.ops.object.camera_add(location=(0, 0, 3))
cam = bpy.context.active_object
cam.data.type = 'ORTHO'
cam.data.ortho_scale = 1.2
cam.rotation_euler = (0, 0, 0)
scene.camera = cam

# Lights
bpy.ops.object.light_add(type='AREA', location=(0.3, -0.3, 2.0))
k = bpy.context.active_object; k.data.energy = 20; k.data.size = 1.5
bpy.ops.object.light_add(type='AREA', location=(-0.3, 0.2, 2.0))
f = bpy.context.active_object; f.data.energy = 12; f.data.size = 1.5
bpy.ops.object.light_add(type='AREA', location=(0, 0, 3.5))
o = bpy.context.active_object; o.data.energy = 15; o.data.size = 1.0

scene.render.filepath = os.path.join(OUTPUT_DIR, 'screw.png')
bpy.ops.render.render(write_still=True)
print("Rendered screw")

# ============================================================
# 2. LED (glowing red)
# ============================================================
scene = setup_scene()
scene.render.resolution_x = 96
scene.render.resolution_y = 96

# LED dome
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, segments=32, ring_count=16, location=(0,0,0.1))
led = bpy.context.active_object
led.scale[2] = 0.5
bpy.ops.object.transform_apply(scale=True)

mat_led = bpy.data.materials.new('LED')
mat_led.use_nodes = True
lt = mat_led.node_tree
lt.nodes.clear()
lo = lt.nodes.new('ShaderNodeOutputMaterial')
lb = lt.nodes.new('ShaderNodeBsdfPrincipled')
lb.inputs['Base Color'].default_value = (1.0, 0.05, 0.02, 1.0)
lb.inputs['Emission Color'].default_value = (1.0, 0.1, 0.02, 1.0)
lb.inputs['Emission Strength'].default_value = 20.0
lb.inputs['Roughness'].default_value = 0.05
lt.links.new(lb.outputs['BSDF'], lo.inputs['Surface'])
led.data.materials.append(mat_led)

# Chrome bezel
bpy.ops.mesh.primitive_torus_add(
    major_radius=0.35, minor_radius=0.06,
    location=(0, 0, 0.0), major_segments=32, minor_segments=12
)
bezel = bpy.context.active_object
mat_b = bpy.data.materials.new('Bezel')
mat_b.use_nodes = True
bb = mat_b.node_tree.nodes['Principled BSDF']
bb.inputs['Base Color'].default_value = (0.7, 0.72, 0.75, 1.0)
bb.inputs['Metallic'].default_value = 0.95
bb.inputs['Roughness'].default_value = 0.1
bezel.data.materials.append(mat_b)

bpy.ops.mesh.primitive_plane_add(size=3, location=(0, 0, -0.06))
sp = bpy.context.active_object
sp.is_shadow_catcher = True

bpy.ops.object.camera_add(location=(0, 0, 3))
cam = bpy.context.active_object
cam.data.type = 'ORTHO'
cam.data.ortho_scale = 1.0
cam.rotation_euler = (0, 0, 0)
scene.camera = cam

bpy.ops.object.light_add(type='AREA', location=(0, 0, 3))
l = bpy.context.active_object; l.data.energy = 8; l.data.size = 1.0
bpy.ops.object.light_add(type='AREA', location=(0.3, -0.2, 2))
l2 = bpy.context.active_object; l2.data.energy = 5; l2.data.size = 0.8

scene.render.filepath = os.path.join(OUTPUT_DIR, 'led.png')
bpy.ops.render.render(write_still=True)
print("Rendered LED")

print("DONE: All hardware rendered")
