"""
Austin's Secret Sauce — VST background v3.
Layout matches Austin's hand-drawn sketch exactly:
- Title with neon border: top center
- Left column: Swell (top), Vinyl (middle), Master (bottom)
- Right column: Psyche (top), LFO (middle), Portrait (bottom-right)
- Portrait fills neon frame tightly (flush against border)
"""

import bpy
import math
import os
from mathutils import Vector

OUTPUT_PATH = '/tmp/aether-art/secret_sauce_v3.png'
PORTRAIT_PATH = '/tmp/aether-art/austin-portrait-square.jpg'
NEON_TITLE_PATH = '/tmp/aether-art/neon_title_v2.png'

RENDER_W = 1020
RENDER_H = 620

# ============================================================
# SCENE SETUP
# ============================================================
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 100
scene.render.resolution_x = RENDER_W
scene.render.resolution_y = RENDER_H
scene.render.film_transparent = False
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'

scene.view_settings.view_transform = 'Filmic'
scene.view_settings.look = 'Medium High Contrast'
scene.view_settings.exposure = 0.0

# ============================================================
# WORLD
# ============================================================
world = bpy.data.worlds.new('World')
scene.world = world
world.use_nodes = True
wn = world.node_tree.nodes
wl = world.node_tree.links
for n in wn: wn.remove(n)

env_tex = wn.new('ShaderNodeTexEnvironment')
env_tex.image = bpy.data.images.load('/tmp/aether-art/outdoor.hdr')
bg = wn.new('ShaderNodeBackground')
bg.inputs['Strength'].default_value = 0.15
out_w = wn.new('ShaderNodeOutputWorld')
wl.new(env_tex.outputs['Color'], bg.inputs['Color'])
wl.new(bg.outputs['Background'], out_w.inputs['Surface'])

# ============================================================
# CAMERA: Top-down orthographic
# ============================================================
bpy.ops.object.camera_add(location=(0, 0, 6))
camera = bpy.context.active_object
camera.data.type = 'ORTHO'
camera.rotation_euler = (0, 0, 0)
camera.data.ortho_scale = 5.1
scene.camera = camera

# ============================================================
# COORDINATE MAPPING
# ============================================================
# Ortho scale 5.1 = width. Aspect 1020/620 = 1.645
# Scene X: -2.55 to +2.55  (5.1 wide)
# Scene Y: -1.55 to +1.55  (3.1 tall)
def gui_to_scene(gx, gy):
    sx = 5.1 / RENDER_W
    sy = (5.1 / (RENDER_W / RENDER_H)) / RENDER_H
    return ((gx - RENDER_W/2) * sx, (RENDER_H/2 - gy) * sy)

# ============================================================
# HELPER: Textured plane
# ============================================================
def make_textured_plane(name, img_path, x, y, z, w, h, emission=0, roughness=0.5):
    bpy.ops.mesh.primitive_plane_add(size=1, location=(x, y, z))
    plane = bpy.context.active_object
    plane.name = name
    plane.scale = (w/2, h/2, 1)
    bpy.ops.object.transform_apply(scale=True)
    
    mat = bpy.data.materials.new(name + '_mat')
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(img_path)
    
    if emission > 0:
        emit = nt.nodes.new('ShaderNodeEmission')
        emit.inputs['Strength'].default_value = emission
        mix = nt.nodes.new('ShaderNodeMixShader')
        transp = nt.nodes.new('ShaderNodeBsdfTransparent')
        nt.links.new(tex.outputs['Color'], emit.inputs['Color'])
        nt.links.new(tex.outputs['Alpha'], mix.inputs['Fac'])
        nt.links.new(transp.outputs['BSDF'], mix.inputs[1])
        nt.links.new(emit.outputs['Emission'], mix.inputs[2])
        nt.links.new(mix.outputs['Shader'], out.inputs['Surface'])
    else:
        bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
        bsdf.inputs['Roughness'].default_value = roughness
        nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
        nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    
    plane.data.materials.append(mat)
    return plane

# ============================================================
# HELPER: Neon tube
# ============================================================
def make_neon_tube(name, points, radius=0.015, emission_strength=15.0, color=(1.0, 0.04, 0.01, 1.0)):
    curve_data = bpy.data.curves.new(name, 'CURVE')
    curve_data.dimensions = '3D'
    curve_data.bevel_depth = radius
    curve_data.bevel_resolution = 6
    
    spline = curve_data.splines.new('POLY')
    spline.points.add(len(points) - 1)
    for i, (x, y, z) in enumerate(points):
        spline.points[i].co = (x, y, z, 1.0)
    
    obj = bpy.data.objects.new(name, curve_data)
    bpy.context.collection.objects.link(obj)
    
    mat = bpy.data.materials.new(name + '_neon')
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    emit = nt.nodes.new('ShaderNodeEmission')
    emit.inputs['Color'].default_value = color
    emit.inputs['Strength'].default_value = emission_strength
    nt.links.new(emit.outputs['Emission'], out.inputs['Surface'])
    
    obj.data.materials.append(mat)
    return obj

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
w_bsdf.inputs['Roughness'].default_value = 0.65

w_coord = wt.nodes.new('ShaderNodeTexCoord')
w_mapping = wt.nodes.new('ShaderNodeMapping')
w_mapping.inputs['Scale'].default_value = (8.0, 1.5, 1.0)

# Wood grain: wave texture
w_wave = wt.nodes.new('ShaderNodeTexWave')
w_wave.wave_type = 'BANDS'
w_wave.bands_direction = 'X'
w_wave.inputs['Scale'].default_value = 2.0
w_wave.inputs['Distortion'].default_value = 10.0
w_wave.inputs['Detail'].default_value = 6.0
w_wave.inputs['Detail Scale'].default_value = 3.0

# Fine noise for grain variation
w_noise = wt.nodes.new('ShaderNodeTexNoise')
w_noise.inputs['Scale'].default_value = 60
w_noise.inputs['Detail'].default_value = 12
w_noise.inputs['Roughness'].default_value = 0.7

# Mix wave + noise
w_mix = wt.nodes.new('ShaderNodeMix')
w_mix.data_type = 'FLOAT'
w_mix.inputs['Factor'].default_value = 0.3

# Color ramp: warm dark wood with visible grain
w_ramp = wt.nodes.new('ShaderNodeValToRGB')
w_ramp.color_ramp.elements[0].position = 0.1
w_ramp.color_ramp.elements[0].color = (0.035, 0.022, 0.012, 1.0)  # lighter dark
mid = w_ramp.color_ramp.elements.new(0.45)
mid.color = (0.065, 0.042, 0.024, 1.0)  # warm mid-tone
w_ramp.color_ramp.elements[1].position = 0.8
w_ramp.color_ramp.elements[1].color = (0.12, 0.08, 0.045, 1.0)  # visible light grain

# Scratch texture (directional)
w_scratch_coord = wt.nodes.new('ShaderNodeTexCoord')
w_scratch_map = wt.nodes.new('ShaderNodeMapping')
w_scratch_map.inputs['Scale'].default_value = (25.0, 2.0, 1.0)

w_scratch = wt.nodes.new('ShaderNodeTexNoise')
w_scratch.inputs['Scale'].default_value = 200
w_scratch.inputs['Detail'].default_value = 15
w_scratch.inputs['Roughness'].default_value = 0.95

# Dings/dents (large low-freq noise)
w_dings = wt.nodes.new('ShaderNodeTexNoise')
w_dings.inputs['Scale'].default_value = 8
w_dings.inputs['Detail'].default_value = 3
w_dings.inputs['Roughness'].default_value = 0.5

# Bump combining grain + scratches + dings
w_bump = wt.nodes.new('ShaderNodeBump')
w_bump.inputs['Strength'].default_value = 0.25
w_bump.inputs['Distance'].default_value = 0.01

w_bump2 = wt.nodes.new('ShaderNodeBump')
w_bump2.inputs['Strength'].default_value = 0.1
w_bump2.inputs['Distance'].default_value = 0.02

# Roughness variation from scratches
w_rough_mix = wt.nodes.new('ShaderNodeMix')
w_rough_mix.data_type = 'FLOAT'
w_rough_mix.inputs['Factor'].default_value = 0.3
w_rough_mix.inputs[2].default_value = 0.6  # base roughness
w_rough_mix.inputs[3].default_value = 0.9  # scratched areas rougher

# Connect wood
wt.links.new(w_coord.outputs['Object'], w_mapping.inputs['Vector'])
wt.links.new(w_mapping.outputs['Vector'], w_wave.inputs['Vector'])
wt.links.new(w_mapping.outputs['Vector'], w_noise.inputs['Vector'])
wt.links.new(w_wave.outputs['Fac'], w_mix.inputs[2])
wt.links.new(w_noise.outputs['Fac'], w_mix.inputs[3])
wt.links.new(w_mix.outputs[0], w_ramp.inputs['Fac'])
wt.links.new(w_ramp.outputs['Color'], w_bsdf.inputs['Base Color'])

# Scratches
wt.links.new(w_scratch_coord.outputs['Object'], w_scratch_map.inputs['Vector'])
wt.links.new(w_scratch_map.outputs['Vector'], w_scratch.inputs['Vector'])
wt.links.new(w_scratch.outputs['Fac'], w_rough_mix.inputs[0])  # factor
wt.links.new(w_rough_mix.outputs[0], w_bsdf.inputs['Roughness'])

# Bumps: grain -> dings
wt.links.new(w_wave.outputs['Fac'], w_bump.inputs['Height'])
wt.links.new(w_dings.outputs['Fac'], w_bump2.inputs['Height'])
wt.links.new(w_bump.outputs['Normal'], w_bump2.inputs['Normal'])
wt.links.new(w_bump2.outputs['Normal'], w_bsdf.inputs['Normal'])

wt.links.new(w_bsdf.outputs['BSDF'], w_out.inputs['Surface'])
wood.data.materials.append(mat_wood)

# ============================================================
# LAYOUT (matching Austin's sketch)
# ============================================================
# Sketch layout:
#   Top center: "Austin's Secret Sauce" [neon border]
#   Left col:  Swell(3) | Vinyl(2) | Master(2)
#   Right col: Psyche(7) | LFO(5+sync) | Portrait [neon border]
#
# GUI dimensions: 1020 x 620
# Title bar: y=0 to ~90
# Left column: x=30 to x=280
# Right column: x=400 to x=990
# Portrait: bottom-right ~150x150px square

# --- TITLE ---
title_cx, title_cy = gui_to_scene(510, 50)
neon_title = make_textured_plane('NeonTitle', NEON_TITLE_PATH,
    title_cx, title_cy, 0.02,
    3.6, 0.48,
    emission=14.0)

# Title neon border
tbw, tbh = 1.95, 0.3
tbz = 0.025
make_neon_tube('TitleBorder', [
    (-tbw, title_cy - tbh, tbz),
    (tbw, title_cy - tbh, tbz),
    (tbw, title_cy + tbh, tbz),
    (-tbw, title_cy + tbh, tbz),
    (-tbw, title_cy - tbh, tbz),
], radius=0.02, emission_strength=18.0)

# --- PORTRAIT (bottom-right, flush against neon border) ---
# Portrait area: roughly 150x150 in GUI, positioned at bottom-right
# Right edge ~990, bottom edge ~600, so center around (905, 525)
port_cx, port_cy = gui_to_scene(910, 520)

# The portrait image needs to fill the neon frame exactly
# Neon tube border with a small gap
port_size_scene = 0.85  # scene units for the square (bigger portrait)

# Neon border half-width -- tube center sits at photo edge
tube_r = 0.018
phw = port_size_scene / 2 + tube_r  # border center at photo edge + tube radius

# Portrait image plane -- fills the border completely
portrait = make_textured_plane('AustinPortrait', PORTRAIT_PATH,
    port_cx, port_cy, 0.01,
    port_size_scene, port_size_scene,
    emission=0, roughness=0.3)
make_neon_tube('PortraitBorder', [
    (port_cx - phw, port_cy - phw, 0.02),
    (port_cx + phw, port_cy - phw, 0.02),
    (port_cx + phw, port_cy + phw, 0.02),
    (port_cx - phw, port_cy + phw, 0.02),
    (port_cx - phw, port_cy - phw, 0.02),
], radius=0.018, emission_strength=15.0)

# --- CRAYON SECTION LABELS ---
# Positions matching sketch layout:
# Left column labels above their knob groups
# Right column labels above their knob groups
labels_info = [
    # (name, gui_x_center, gui_y)
    ('SWELL',  130, 105),    # left col, top section
    ('VINYL',  130, 250),    # left col, middle section
    ('MASTER', 100, 400),    # left col, bottom section
    ('PSYCHE', 600, 105),    # right col, top section
    ('LFO',    600, 250),    # right col, middle section
]

for label_name, gx, gy in labels_info:
    lx, ly = gui_to_scene(gx, gy)
    make_textured_plane(f'Label_{label_name}',
        f'/tmp/aether-art/crayon_{label_name.lower()}_v2.png',
        lx, ly, 0.005,
        0.8, 0.2,
        emission=2.5)

# ============================================================
# OUTER BORDER (subtle neon frame around entire plugin)
# ============================================================
obw, obh = 2.5, 1.52
make_neon_tube('OuterBorder', [
    (-obw, -obh, 0.015),
    (obw, -obh, 0.015),
    (obw, obh, 0.015),
    (-obw, obh, 0.015),
    (-obw, -obh, 0.015),
], radius=0.012, emission_strength=6.0, color=(1.0, 0.04, 0.01, 1.0))

# ============================================================
# LIGHTING
# ============================================================
# Warm fill (dim -- neon should dominate)
bpy.ops.object.light_add(type='AREA', location=(0, 0, 4))
fill = bpy.context.active_object
fill.name = 'Fill'
fill.data.energy = 18
fill.data.size = 8.0
fill.data.color = (0.95, 0.88, 0.82)  # warm

# Spot on portrait area
bpy.ops.object.light_add(type='SPOT', location=(port_cx, port_cy, 2.5))
spot = bpy.context.active_object
spot.name = 'PortraitSpot'
spot.data.energy = 25
spot.data.spot_size = math.radians(25)
spot.data.spot_blend = 0.5

# ============================================================
# RENDER
# ============================================================
scene.render.filepath = OUTPUT_PATH
bpy.ops.render.render(write_still=True)
print(f"DONE: Secret Sauce v3 rendered to {OUTPUT_PATH}")
