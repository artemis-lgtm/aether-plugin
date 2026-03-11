"""
Austin's Secret Sauce — Full VST background render in Blender.
- Dark beat-up wood surface
- Red neon "Austin's Secret Sauce" title text (emissive tubes)
- Red neon border around title
- Red neon border around Austin's portrait (bottom-right)
- Austin's portrait UV-mapped into the photo frame
- Crayon-textured section labels (SWELL, VINYL, PSYCHE, LFO, MASTER)
- Empty knob areas for JUCE overlay
"""

import bpy
import bmesh
import math
import os
from mathutils import Vector

OUTPUT_PATH = '/tmp/aether-art/secret_sauce_bg.png'
PORTRAIT_PATH = '/Users/artemis/.openclaw/workspace/projects/aether/resources/austin-portrait.jpg'

RENDER_W = 1020
RENDER_H = 620

# ============================================================
# SCENE SETUP
# ============================================================
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 128
scene.render.resolution_x = RENDER_W
scene.render.resolution_y = RENDER_H
scene.render.film_transparent = False
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'

# Filmic for better highlights (neon glow)
scene.view_settings.view_transform = 'Filmic'
scene.view_settings.look = 'Medium High Contrast'
scene.view_settings.exposure = 0.0

# Compositor setup deferred to end of script

# ============================================================
# WORLD: Dark moody environment
# ============================================================
world = bpy.data.worlds.new('World')
scene.world = world
world.use_nodes = True
wn = world.node_tree.nodes
wl = world.node_tree.links
for n in wn: wn.remove(n)

# Dark HDRI for subtle reflections on neon tubes
env_tex = wn.new('ShaderNodeTexEnvironment')
env_tex.image = bpy.data.images.load('/tmp/aether-art/outdoor.hdr')

bg = wn.new('ShaderNodeBackground')
bg.inputs['Strength'].default_value = 0.3  # very dark -- neon is the star

out_w = wn.new('ShaderNodeOutputWorld')
wl.new(env_tex.outputs['Color'], bg.inputs['Color'])
wl.new(bg.outputs['Background'], out_w.inputs['Surface'])

# ============================================================
# DARK BEAT-UP WOOD SURFACE
# ============================================================
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
wood = bpy.context.active_object
wood.name = 'WoodSurface'

mat_wood = bpy.data.materials.new('DarkWood')
mat_wood.use_nodes = True
wt = mat_wood.node_tree
wt.nodes.clear()

w_out = wt.nodes.new('ShaderNodeOutputMaterial')
w_bsdf = wt.nodes.new('ShaderNodeBsdfPrincipled')
w_bsdf.inputs['Roughness'].default_value = 0.7

# Wood grain using wave + noise (dark, beaten up)
w_coord = wt.nodes.new('ShaderNodeTexCoord')
w_mapping = wt.nodes.new('ShaderNodeMapping')
w_mapping.inputs['Scale'].default_value = (6.0, 1.0, 1.0)

w_wave = wt.nodes.new('ShaderNodeTexWave')
w_wave.wave_type = 'BANDS'
w_wave.bands_direction = 'X'
w_wave.inputs['Scale'].default_value = 3.0
w_wave.inputs['Distortion'].default_value = 6.0
w_wave.inputs['Detail'].default_value = 4.0
w_wave.inputs['Detail Scale'].default_value = 2.0

w_noise = wt.nodes.new('ShaderNodeTexNoise')
w_noise.inputs['Scale'].default_value = 40
w_noise.inputs['Detail'].default_value = 10
w_noise.inputs['Roughness'].default_value = 0.7

# Mix wave + noise for wood
w_mix = wt.nodes.new('ShaderNodeMix')
w_mix.data_type = 'FLOAT'
w_mix.inputs['Factor'].default_value = 0.35

# Color ramp for dark wood tones
w_ramp = wt.nodes.new('ShaderNodeValToRGB')
w_ramp.color_ramp.elements[0].position = 0.2
w_ramp.color_ramp.elements[0].color = (0.02, 0.012, 0.008, 1.0)  # very dark
w_ramp.color_ramp.elements[1].position = 0.8
w_ramp.color_ramp.elements[1].color = (0.06, 0.04, 0.025, 1.0)  # slightly lighter grain

# Scratches/dings overlay
w_scratch = wt.nodes.new('ShaderNodeTexNoise')
w_scratch.inputs['Scale'].default_value = 200
w_scratch.inputs['Detail'].default_value = 15
w_scratch.inputs['Roughness'].default_value = 0.9

w_scratch_ramp = wt.nodes.new('ShaderNodeValToRGB')
w_scratch_ramp.color_ramp.elements[0].position = 0.45
w_scratch_ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
w_scratch_ramp.color_ramp.elements[1].position = 0.55
w_scratch_ramp.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)

# Roughness variation from scratches
w_rough_map = wt.nodes.new('ShaderNodeMapRange')
w_rough_map.inputs['To Min'].default_value = 0.5
w_rough_map.inputs['To Max'].default_value = 0.85

# Bump for wood grain
w_bump = wt.nodes.new('ShaderNodeBump')
w_bump.inputs['Strength'].default_value = 0.15
w_bump.inputs['Distance'].default_value = 0.01

# Connect wood shader
wt.links.new(w_coord.outputs['Object'], w_mapping.inputs['Vector'])
wt.links.new(w_mapping.outputs['Vector'], w_wave.inputs['Vector'])
wt.links.new(w_mapping.outputs['Vector'], w_noise.inputs['Vector'])
wt.links.new(w_wave.outputs['Fac'], w_mix.inputs[2])
wt.links.new(w_noise.outputs['Fac'], w_mix.inputs[3])
wt.links.new(w_mix.outputs[0], w_ramp.inputs['Fac'])
wt.links.new(w_ramp.outputs['Color'], w_bsdf.inputs['Base Color'])
wt.links.new(w_scratch.outputs['Fac'], w_scratch_ramp.inputs['Fac'])
wt.links.new(w_scratch_ramp.outputs['Color'], w_rough_map.inputs['Value'])
wt.links.new(w_rough_map.outputs['Result'], w_bsdf.inputs['Roughness'])
wt.links.new(w_wave.outputs['Fac'], w_bump.inputs['Height'])
wt.links.new(w_bump.outputs['Normal'], w_bsdf.inputs['Normal'])
wt.links.new(w_bsdf.outputs['BSDF'], w_out.inputs['Surface'])

wood.data.materials.append(mat_wood)

# ============================================================
# NEON MATERIAL (reusable)
# ============================================================
def make_neon_material(name, color=(1.0, 0.05, 0.02, 1.0), strength=15.0):
    """Create a glowing neon tube material."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    emit = nt.nodes.new('ShaderNodeEmission')
    emit.inputs['Color'].default_value = color
    emit.inputs['Strength'].default_value = strength
    
    # Mix emission with slight glass for tube look
    glass = nt.nodes.new('ShaderNodeBsdfGlass')
    glass.inputs['Color'].default_value = (1.0, 0.95, 0.95, 1.0)
    glass.inputs['Roughness'].default_value = 0.0
    glass.inputs['IOR'].default_value = 1.5
    
    mix = nt.nodes.new('ShaderNodeMixShader')
    mix.inputs['Fac'].default_value = 0.15  # mostly emission, slight glass
    
    nt.links.new(emit.outputs['Emission'], mix.inputs[1])
    nt.links.new(glass.outputs['BSDF'], mix.inputs[2])
    nt.links.new(mix.outputs['Shader'], out.inputs['Surface'])
    
    return mat

mat_neon_red = make_neon_material('NeonRed', (1.0, 0.04, 0.01, 1.0), 20.0)
mat_neon_red_dim = make_neon_material('NeonRedDim', (1.0, 0.04, 0.01, 1.0), 8.0)

# ============================================================
# NEON TEXT: "Austin's Secret Sauce"
# ============================================================
# Create text object
bpy.ops.object.text_add(location=(0, 0.8, 0.15))
text_obj = bpy.context.active_object
text_obj.name = 'NeonTitle'
text_obj.data.body = "Austin's Secret Sauce"
text_obj.data.size = 0.28
text_obj.data.align_x = 'CENTER'
text_obj.data.align_y = 'CENTER'

# Extrude for tube thickness
text_obj.data.extrude = 0.025
text_obj.data.bevel_depth = 0.018
text_obj.data.bevel_resolution = 4

# Try to use a script/handwriting font if available
try:
    for f_name in bpy.data.fonts:
        pass  # check available fonts
    # Use built-in Bfont (Blender's default) -- it's clean enough for neon
except:
    pass

text_obj.data.materials.append(mat_neon_red)
text_obj.rotation_euler = (math.radians(90), 0, 0)  # lay flat, face up

# ============================================================
# NEON BORDER AROUND TITLE
# ============================================================
def make_neon_border(name, width, height, z, tube_radius=0.012, mat=None):
    """Create a rectangular neon tube border."""
    hw = width / 2
    hh = height / 2
    
    # Create curve for the border rectangle
    curve_data = bpy.data.curves.new(name, 'CURVE')
    curve_data.dimensions = '3D'
    curve_data.bevel_depth = tube_radius
    curve_data.bevel_resolution = 6
    curve_data.use_fill_caps = True
    
    spline = curve_data.splines.new('POLY')
    # Rectangle with rounded feel (4 corners + closure)
    coords = [
        (-hw, -hh, z), (hw, -hh, z), (hw, hh, z), (-hw, hh, z), (-hw, -hh, z)
    ]
    spline.points.add(len(coords) - 1)
    for i, (x, y, zz) in enumerate(coords):
        spline.points[i].co = (x, y, zz, 1.0)
    
    border_obj = bpy.data.objects.new(name, curve_data)
    bpy.context.collection.objects.link(border_obj)
    if mat:
        border_obj.data.materials.append(mat)
    
    return border_obj

# Title border -- positioned around the text
title_border = make_neon_border('TitleBorder', 4.2, 0.65, 0.12, 0.015, mat_neon_red)
title_border.location = (0, 0.8, 0)

# ============================================================
# AUSTIN'S PORTRAIT + NEON BORDER
# ============================================================
# Portrait frame (bottom-right area of the GUI)
# In GUI coords: roughly right side, lower area
portrait_x = 2.0   # right side
portrait_y = -1.0   # bottom area
portrait_size = 0.6

bpy.ops.mesh.primitive_plane_add(size=portrait_size, location=(portrait_x, portrait_y, 0.01))
portrait_plane = bpy.context.active_object
portrait_plane.name = 'AustinPortrait'

# Portrait material with the ChatGPT image
mat_portrait = bpy.data.materials.new('PortraitMat')
mat_portrait.use_nodes = True
pt = mat_portrait.node_tree
pt.nodes.clear()

p_out = pt.nodes.new('ShaderNodeOutputMaterial')
p_bsdf = pt.nodes.new('ShaderNodeBsdfPrincipled')
p_bsdf.inputs['Roughness'].default_value = 0.3
p_bsdf.inputs['Specular IOR Level'].default_value = 0.3

p_tex = pt.nodes.new('ShaderNodeTexImage')
p_tex.image = bpy.data.images.load(PORTRAIT_PATH)

pt.links.new(p_tex.outputs['Color'], p_bsdf.inputs['Base Color'])
pt.links.new(p_bsdf.outputs['BSDF'], p_out.inputs['Surface'])

portrait_plane.data.materials.append(mat_portrait)

# Neon border around portrait
portrait_border = make_neon_border('PortraitBorder', 
    portrait_size + 0.08, portrait_size + 0.08, 0.02, 0.012, mat_neon_red)
portrait_border.location = (portrait_x, portrait_y, 0)

# ============================================================
# CRAYON SECTION LABELS
# ============================================================
def make_crayon_label(text, x, y, size=0.18):
    """Create a crayon-textured section label."""
    bpy.ops.object.text_add(location=(x, y, 0.01))
    obj = bpy.context.active_object
    obj.name = f'Label_{text}'
    obj.data.body = text
    obj.data.size = size
    obj.data.align_x = 'CENTER'
    obj.data.extrude = 0.003
    obj.data.bevel_depth = 0.002
    obj.data.bevel_resolution = 1
    obj.rotation_euler = (math.radians(90), 0, 0)
    
    # Crayon material -- rough, waxy, slightly transparent
    mat = bpy.data.materials.new(f'Crayon_{text}')
    mat.use_nodes = True
    ct = mat.node_tree
    ct.nodes.clear()
    
    c_out = ct.nodes.new('ShaderNodeOutputMaterial')
    c_bsdf = ct.nodes.new('ShaderNodeBsdfPrincipled')
    
    # Crayon colors per section
    colors = {
        'SWELL': (0.95, 0.3, 0.35, 1.0),    # red-pink crayon
        'VINYL': (0.2, 0.7, 0.3, 1.0),       # green crayon
        'PSYCHE': (0.6, 0.2, 0.85, 1.0),     # purple crayon
        'LFO': (0.1, 0.5, 0.95, 1.0),        # blue crayon
        'MASTER': (0.95, 0.75, 0.1, 1.0),    # yellow crayon
    }
    
    color = colors.get(text, (1.0, 1.0, 1.0, 1.0))
    c_bsdf.inputs['Base Color'].default_value = color
    c_bsdf.inputs['Roughness'].default_value = 0.85  # waxy/matte like crayon
    c_bsdf.inputs['Specular IOR Level'].default_value = 0.2
    
    # Waxy bump for crayon texture
    c_noise = ct.nodes.new('ShaderNodeTexNoise')
    c_noise.inputs['Scale'].default_value = 100
    c_noise.inputs['Detail'].default_value = 8
    c_noise.inputs['Roughness'].default_value = 0.8
    
    c_bump = ct.nodes.new('ShaderNodeBump')
    c_bump.inputs['Strength'].default_value = 0.3
    c_bump.inputs['Distance'].default_value = 0.005
    
    ct.links.new(c_noise.outputs['Fac'], c_bump.inputs['Height'])
    ct.links.new(c_bump.outputs['Normal'], c_bsdf.inputs['Normal'])
    ct.links.new(c_bsdf.outputs['BSDF'], c_out.inputs['Surface'])
    
    obj.data.materials.append(mat)
    return obj

# Position labels roughly matching the GUI layout
# GUI is 1020x620, scene coords roughly: x=-2.5 to 2.5, y=-1.5 to 1.5
# Scale factor: ~5.0/1020 in x, ~3.0/620 in y
sx = 5.0 / 1020  # scene x per pixel
sy = 3.0 / 620   # scene y per pixel

# Section positions (from JUCE layout, converted to scene coords)
# Center of GUI = (510, 310) = scene (0, 0)
def gui_to_scene(gx, gy):
    return ((gx - 510) * sx, (310 - gy) * sy)

# Labels above their knob sections
swell_pos = gui_to_scene(100, 110)    # above swell knobs
vinyl_pos = gui_to_scene(270, 110)    # above vinyl knobs
psyche_pos = gui_to_scene(555, 110)   # above psyche knobs
lfo_pos = gui_to_scene(795, 110)      # above LFO knobs
master_pos = gui_to_scene(510, 360)   # above master knobs

make_crayon_label('SWELL', swell_pos[0], swell_pos[1])
make_crayon_label('VINYL', vinyl_pos[0], vinyl_pos[1])
make_crayon_label('PSYCHE', psyche_pos[0], psyche_pos[1])
make_crayon_label('LFO', lfo_pos[0], lfo_pos[1])
make_crayon_label('MASTER', master_pos[0], master_pos[1])

# ============================================================
# CAMERA: Top-down (orthographic for pixel-perfect JUCE alignment)
# ============================================================
bpy.ops.object.camera_add(location=(0, 0, 6))
camera = bpy.context.active_object
camera.data.type = 'ORTHO'
camera.rotation_euler = (0, 0, 0)

# Frame to exactly match 1020x620 aspect ratio
aspect = RENDER_W / RENDER_H
camera.data.ortho_scale = 5.1  # width of view in Blender units
scene.camera = camera

# ============================================================
# LIGHTING: Moody, neon-focused
# ============================================================
# Subtle overhead fill (very dim -- let neon dominate)
bpy.ops.object.light_add(type='AREA', location=(0, 0, 4))
fill = bpy.context.active_object
fill.name = 'Fill'
fill.data.energy = 15
fill.data.size = 6.0
fill.data.color = (0.9, 0.85, 0.8)  # warm

# Neon glow handled by high emission strength + Cycles light bounces
# No compositor glare needed -- the emission at 20+ will naturally illuminate surroundings

# ============================================================
# RENDER
# ============================================================
scene.render.filepath = OUTPUT_PATH
bpy.ops.render.render(write_still=True)
print(f"DONE: Secret Sauce background rendered to {OUTPUT_PATH}")
