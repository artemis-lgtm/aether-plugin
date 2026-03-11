"""
Austin's Secret Sauce — VST background v2.
Uses pre-rendered text images (neon title + crayon labels) on emissive planes.
"""

import bpy
import math
import os
from mathutils import Vector

OUTPUT_PATH = '/tmp/aether-art/secret_sauce_v2.png'
PORTRAIT_PATH = '/Users/artemis/.openclaw/workspace/projects/aether/resources/austin-portrait.jpg'
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
# WORLD: Very dark
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
bg.inputs['Strength'].default_value = 0.15  # very dark
out_w = wn.new('ShaderNodeOutputWorld')
wl.new(env_tex.outputs['Color'], bg.inputs['Color'])
wl.new(bg.outputs['Background'], out_w.inputs['Surface'])

# ============================================================
# HELPER: Create textured plane
# ============================================================
def make_textured_plane(name, img_path, x, y, z, w, h, emission=0, roughness=0.5):
    """Create a plane with an image texture."""
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
        # Emissive plane (for neon text)
        emit = nt.nodes.new('ShaderNodeEmission')
        emit.inputs['Strength'].default_value = emission
        
        # Use alpha for transparency
        mix = nt.nodes.new('ShaderNodeMixShader')
        transp = nt.nodes.new('ShaderNodeBsdfTransparent')
        
        nt.links.new(tex.outputs['Color'], emit.inputs['Color'])
        nt.links.new(tex.outputs['Alpha'], mix.inputs['Fac'])
        nt.links.new(transp.outputs['BSDF'], mix.inputs[1])
        nt.links.new(emit.outputs['Emission'], mix.inputs[2])
        nt.links.new(mix.outputs['Shader'], out.inputs['Surface'])
    else:
        # Regular textured plane
        bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
        bsdf.inputs['Roughness'].default_value = roughness
        nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
        nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    
    plane.data.materials.append(mat)
    return plane

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

# Wood grain
w_coord = wt.nodes.new('ShaderNodeTexCoord')
w_mapping = wt.nodes.new('ShaderNodeMapping')
w_mapping.inputs['Scale'].default_value = (6.0, 1.0, 1.0)

w_wave = wt.nodes.new('ShaderNodeTexWave')
w_wave.wave_type = 'BANDS'
w_wave.bands_direction = 'X'
w_wave.inputs['Scale'].default_value = 2.5
w_wave.inputs['Distortion'].default_value = 8.0
w_wave.inputs['Detail'].default_value = 5.0

w_noise = wt.nodes.new('ShaderNodeTexNoise')
w_noise.inputs['Scale'].default_value = 40
w_noise.inputs['Detail'].default_value = 10
w_noise.inputs['Roughness'].default_value = 0.7

w_mix = wt.nodes.new('ShaderNodeMix')
w_mix.data_type = 'FLOAT'
w_mix.inputs['Factor'].default_value = 0.35

w_ramp = wt.nodes.new('ShaderNodeValToRGB')
w_ramp.color_ramp.elements[0].position = 0.15
w_ramp.color_ramp.elements[0].color = (0.025, 0.015, 0.008, 1.0)  # warm dark brown
w_ramp.color_ramp.elements[1].position = 0.75
w_ramp.color_ramp.elements[1].color = (0.08, 0.055, 0.03, 1.0)  # visible warm grain

# Scratches
w_scratch = wt.nodes.new('ShaderNodeTexNoise')
w_scratch.inputs['Scale'].default_value = 300
w_scratch.inputs['Detail'].default_value = 15
w_scratch.inputs['Roughness'].default_value = 0.95

w_scratch_map = wt.nodes.new('ShaderNodeMapping')
w_scratch_map.inputs['Scale'].default_value = (20.0, 1.0, 1.0)  # directional scratches

# Bump for grain + scratches
w_bump = wt.nodes.new('ShaderNodeBump')
w_bump.inputs['Strength'].default_value = 0.2
w_bump.inputs['Distance'].default_value = 0.01

# Connect
wt.links.new(w_coord.outputs['Object'], w_mapping.inputs['Vector'])
wt.links.new(w_mapping.outputs['Vector'], w_wave.inputs['Vector'])
wt.links.new(w_mapping.outputs['Vector'], w_noise.inputs['Vector'])
wt.links.new(w_wave.outputs['Fac'], w_mix.inputs[2])
wt.links.new(w_noise.outputs['Fac'], w_mix.inputs[3])
wt.links.new(w_mix.outputs[0], w_ramp.inputs['Fac'])
wt.links.new(w_ramp.outputs['Color'], w_bsdf.inputs['Base Color'])
wt.links.new(w_coord.outputs['Object'], w_scratch_map.inputs['Vector'])
wt.links.new(w_scratch_map.outputs['Vector'], w_scratch.inputs['Vector'])
wt.links.new(w_scratch.outputs['Fac'], w_bump.inputs['Height'])
wt.links.new(w_bump.outputs['Normal'], w_bsdf.inputs['Normal'])
wt.links.new(w_bsdf.outputs['BSDF'], w_out.inputs['Surface'])

wood.data.materials.append(mat_wood)

# ============================================================
# COORDINATE MAPPING: GUI pixels -> Blender scene units
# ============================================================
# Camera ortho_scale = 5.1 (width), aspect = 1020/620
# Scene X: -2.55 to +2.55
# Scene Y: -1.55 to +1.55
def gui_to_scene(gx, gy):
    """Convert GUI pixel coords (1020x620) to Blender scene coords."""
    sx = 5.1 / RENDER_W
    sy = (5.1 / (RENDER_W / RENDER_H)) / RENDER_H
    return ((gx - RENDER_W/2) * sx, (RENDER_H/2 - gy) * sy)

# ============================================================
# NEON TITLE: "Austin's Secret Sauce"
# ============================================================
# Title area: top center, with padding from edge
title_x, title_y = gui_to_scene(510, 65)
neon_title = make_textured_plane('NeonTitle', NEON_TITLE_PATH,
    title_x, title_y, 0.02,
    3.8, 0.55,
    emission=12.0)  # brighter neon

# ============================================================
# NEON BORDER AROUND TITLE
# ============================================================
def make_neon_tube(name, points, radius=0.015, emission_strength=15.0):
    """Create a neon tube along a path."""
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
    
    # Neon emission material
    mat = bpy.data.materials.new(name + '_neon')
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    emit = nt.nodes.new('ShaderNodeEmission')
    emit.inputs['Color'].default_value = (1.0, 0.04, 0.01, 1.0)  # deep red
    emit.inputs['Strength'].default_value = emission_strength
    nt.links.new(emit.outputs['Emission'], out.inputs['Surface'])
    
    obj.data.materials.append(mat)
    return obj

# Title border rectangle
tbw, tbh = 2.05, 0.32  # half-widths (slightly smaller to stay in bounds)
tbz = 0.025
title_border = make_neon_tube('TitleBorder', [
    (-tbw, title_y - tbh, tbz),
    (tbw, title_y - tbh, tbz),
    (tbw, title_y + tbh, tbz),
    (-tbw, title_y + tbh, tbz),
    (-tbw, title_y - tbh, tbz),
], radius=0.02, emission_strength=15.0)

# ============================================================
# AUSTIN'S PORTRAIT (bottom-right)
# ============================================================
# Bottom-right area of GUI: roughly (850, 480) center
port_x, port_y = gui_to_scene(850, 470)
portrait = make_textured_plane('AustinPortrait', PORTRAIT_PATH,
    port_x, port_y, 0.01,
    0.85, 0.85,  # fills the border tightly
    emission=0, roughness=0.3)

# Neon border around portrait (tight around photo)
pbw, pbh = 0.47, 0.47
portrait_border = make_neon_tube('PortraitBorder', [
    (port_x - pbw, port_y - pbh, 0.02),
    (port_x + pbw, port_y - pbh, 0.02),
    (port_x + pbw, port_y + pbh, 0.02),
    (port_x - pbw, port_y + pbh, 0.02),
    (port_x - pbw, port_y - pbh, 0.02),
], radius=0.015, emission_strength=12.0)

# ============================================================
# CRAYON SECTION LABELS
# ============================================================
labels_info = [
    ('SWELL', 130, 108),    # moved inward
    ('VINYL', 290, 108),
    ('PSYCHE', 555, 108),
    ('LFO', 795, 108),
    ('MASTER', 440, 355),   # moved left (away from portrait)
]

for label_name, gx, gy in labels_info:
    lx, ly = gui_to_scene(gx, gy)
    make_textured_plane(f'Label_{label_name}',
        f'/tmp/aether-art/crayon_{label_name.lower()}_v2.png',
        lx, ly, 0.005,
        0.8, 0.2,
        emission=2.0)  # brighter -- visible on dark wood

# ============================================================
# CAMERA: Top-down orthographic (pixel-perfect JUCE alignment)
# ============================================================
bpy.ops.object.camera_add(location=(0, 0, 6))
camera = bpy.context.active_object
camera.data.type = 'ORTHO'
camera.rotation_euler = (0, 0, 0)
camera.data.ortho_scale = 5.1
scene.camera = camera

# ============================================================
# LIGHTING: Moody, neon-dominant
# ============================================================
# Very subtle fill light
bpy.ops.object.light_add(type='AREA', location=(0, 0, 4))
fill = bpy.context.active_object
fill.name = 'Fill'
fill.data.energy = 10
fill.data.size = 8.0
fill.data.color = (0.9, 0.85, 0.8)

# Spot on portrait
bpy.ops.object.light_add(type='SPOT', location=(port_x, port_y, 2.5))
spot = bpy.context.active_object
spot.name = 'PortraitSpot'
spot.data.energy = 30
spot.data.spot_size = math.radians(30)
spot.data.spot_blend = 0.5
spot.rotation_euler = (0, 0, 0)

# ============================================================
# RENDER
# ============================================================
scene.render.filepath = OUTPUT_PATH
bpy.ops.render.render(write_still=True)
print(f"DONE: Secret Sauce v2 rendered to {OUTPUT_PATH}")
