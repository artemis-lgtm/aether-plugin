"""
Render a chrome nameplate with "Austin's Secret Sauce" etched into it.
And a chrome portrait frame. Both photorealistic via Blender Cycles.
"""
import bpy
import os
import math

# ---- Clean scene ----
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'GPU'
scene.cycles.samples = 512
scene.render.film_transparent = True

# ---- Chrome Material ----
def make_chrome_mat(name="Chrome"):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out = nodes.new('ShaderNodeOutputMaterial')
    out.location = (400, 0)

    # Principled BSDF with metallic chrome
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (0.85, 0.85, 0.88, 1.0)
    bsdf.inputs['Metallic'].default_value = 1.0
    bsdf.inputs['Roughness'].default_value = 0.08
    bsdf.inputs['IOR'].default_value = 2.5
    # Specular tint for chrome
    if 'Specular Tint' in bsdf.inputs:
        bsdf.inputs['Specular Tint'].default_value = (1.0, 1.0, 1.0, 1.0)

    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat

def make_etched_mat(name="Etched"):
    """Darker, rougher material for etched text."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out = nodes.new('ShaderNodeOutputMaterial')
    out.location = (400, 0)

    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (0.15, 0.15, 0.18, 1.0)
    bsdf.inputs['Metallic'].default_value = 0.9
    bsdf.inputs['Roughness'].default_value = 0.6
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat

chrome_mat = make_chrome_mat()
etched_mat = make_etched_mat()

# ================================================================
# TITLE PLATE: "Austin's Secret Sauce"
# Target: 561x83 pixels -> aspect ratio ~6.76:1
# ================================================================
plate_w, plate_h, plate_d = 6.76, 1.0, 0.15

# Main plate body
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
plate = bpy.context.active_object
plate.name = "TitlePlate"
plate.scale = (plate_w / 2, plate_h / 2, plate_d / 2)
bpy.ops.object.transform_apply(scale=True)

# Add bevel for rounded edges
bevel = plate.modifiers.new(name="Bevel", type='BEVEL')
bevel.width = 0.04
bevel.segments = 3
bpy.ops.object.modifier_apply(modifier="Bevel")

plate.data.materials.append(chrome_mat)

# Etched text
bpy.ops.object.text_add(location=(0, 0, plate_d / 2 + 0.001))
text_obj = bpy.context.active_object
text_obj.name = "TitleText"
text_obj.data.body = "Austin's Secret Sauce"
text_obj.data.align_x = 'CENTER'
text_obj.data.align_y = 'CENTER'
text_obj.data.size = 0.38
text_obj.data.extrude = 0.012

# Try to find a nice serif/script font
font_paths = [
    "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf",
    "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
    "/System/Library/Fonts/Supplemental/Copperplate.ttc",
    "/System/Library/Fonts/NewYork.ttf",
]
for fp in font_paths:
    if os.path.exists(fp):
        try:
            text_obj.data.font = bpy.data.fonts.load(fp)
            break
        except:
            pass

# Boolean subtract the text into the plate for etched effect
bpy.ops.object.select_all(action='DESELECT')
text_obj.select_set(True)
bpy.context.view_layer.objects.active = text_obj
bpy.ops.object.convert(target='MESH')

# Position text slightly into plate
text_obj.location.z = plate_d / 2 - 0.005

# Give text etched material
text_obj.data.materials.append(etched_mat)

# ---- Lighting for chrome reflections ----
# Key light (warm)
bpy.ops.object.light_add(type='AREA', location=(3, -3, 5))
key = bpy.context.active_object
key.name = "KeyLight"
key.data.energy = 300
key.data.size = 4
key.data.color = (1.0, 0.95, 0.9)
key.rotation_euler = (math.radians(45), 0, math.radians(30))

# Fill light (cool)
bpy.ops.object.light_add(type='AREA', location=(-3, -2, 3))
fill = bpy.context.active_object
fill.name = "FillLight"
fill.data.energy = 150
fill.data.size = 3
fill.data.color = (0.9, 0.92, 1.0)
fill.rotation_euler = (math.radians(50), 0, math.radians(-40))

# Rim light
bpy.ops.object.light_add(type='AREA', location=(0, 3, 2))
rim = bpy.context.active_object
rim.name = "RimLight"
rim.data.energy = 100
rim.data.size = 5
rim.rotation_euler = (math.radians(-30), 0, 0)

# HDRI-like environment
world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
wnodes = world.node_tree.nodes
wlinks = world.node_tree.links
wnodes.clear()
wout = wnodes.new('ShaderNodeOutputWorld')
wbg = wnodes.new('ShaderNodeBackground')
wbg.inputs['Color'].default_value = (0.3, 0.3, 0.35, 1.0)
wbg.inputs['Strength'].default_value = 0.5
wlinks.new(wbg.outputs['Background'], wout.inputs['Surface'])

# ---- Camera (top-down, slight angle for depth) ----
bpy.ops.object.camera_add(location=(0, -0.3, 5.5))
cam = bpy.context.active_object
cam.name = "Camera"
cam.rotation_euler = (math.radians(3), 0, 0)
cam.data.lens = 80
cam.data.type = 'PERSP'
scene.camera = cam

# ---- Render title plate ----
scene.render.resolution_x = 1122  # 2x for quality (561*2)
scene.render.resolution_y = 166   # 2x (83*2)
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.render.filepath = '/tmp/aether-art/chrome_title_raw.png'
bpy.ops.render.render(write_still=True)

# ================================================================
# PORTRAIT FRAME: Chrome border frame
# Target: 175x175 pixels (square)
# ================================================================

# Hide title objects
plate.hide_render = True
text_obj.hide_render = True

frame_size = 2.0
frame_border = 0.2
frame_depth = 0.12

# Outer frame
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
outer = bpy.context.active_object
outer.name = "FrameOuter"
outer.scale = (frame_size / 2, frame_size / 2, frame_depth / 2)
bpy.ops.object.transform_apply(scale=True)
bevel2 = outer.modifiers.new(name="Bevel", type='BEVEL')
bevel2.width = 0.03
bevel2.segments = 3
bpy.ops.object.modifier_apply(modifier="Bevel")
outer.data.materials.append(chrome_mat)

# Inner cutout (dark recess)
inner_s = frame_size - frame_border * 2
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, frame_depth * 0.1))
inner = bpy.context.active_object
inner.name = "FrameInner"
inner.scale = (inner_s / 2, inner_s / 2, frame_depth / 2 + 0.01)
bpy.ops.object.transform_apply(scale=True)
inner.data.materials.append(etched_mat)

# Adjust camera for square frame
cam.location = (0, -0.2, 4.0)
cam.data.lens = 60
cam.rotation_euler = (math.radians(3), 0, 0)

scene.render.resolution_x = 350   # 2x
scene.render.resolution_y = 350   # 2x
scene.render.filepath = '/tmp/aether-art/chrome_frame_raw.png'
bpy.ops.render.render(write_still=True)

print("DONE: chrome_title_raw.png + chrome_frame_raw.png")
