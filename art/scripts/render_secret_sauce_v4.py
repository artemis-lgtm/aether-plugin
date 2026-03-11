"""
Austin's Secret Sauce — VST background v4.
COMPACT layout -- everything packed tight, no wasted space.
Layout from Austin's sketch: Title top, Left: Swell/Vinyl/Master, Right: Psyche/LFO, Portrait bottom-right.
Portrait fills neon frame flush.
Warmer, more visible wood grain.
"""

import bpy
import math

OUTPUT_PATH = '/tmp/aether-art/secret_sauce_v4.png'
PORTRAIT_PATH = '/tmp/aether-art/austin-portrait-square.jpg'
NEON_TITLE_PATH = '/tmp/aether-art/neon_title_v2.png'

RENDER_W = 1020
RENDER_H = 620

# ============================================================
# SCENE
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
# CAMERA
# ============================================================
bpy.ops.object.camera_add(location=(0, 0, 6))
camera = bpy.context.active_object
camera.data.type = 'ORTHO'
camera.rotation_euler = (0, 0, 0)
camera.data.ortho_scale = 5.1
scene.camera = camera

# ============================================================
# COORD MAPPING
# ============================================================
def gui_to_scene(gx, gy):
    sx = 5.1 / RENDER_W
    sy = (5.1 / (RENDER_W / RENDER_H)) / RENDER_H
    return ((gx - RENDER_W/2) * sx, (RENDER_H/2 - gy) * sy)

# ============================================================
# HELPERS
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

def make_neon_tube(name, points, radius=0.015, strength=15.0, color=(1.0, 0.04, 0.01, 1.0)):
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
    emit.inputs['Strength'].default_value = strength
    nt.links.new(emit.outputs['Emission'], out.inputs['Surface'])
    obj.data.materials.append(mat)
    return obj

# ============================================================
# DARK WOOD SURFACE (warm, beat-up, visible grain)
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

w_wave = wt.nodes.new('ShaderNodeTexWave')
w_wave.wave_type = 'BANDS'
w_wave.bands_direction = 'X'
w_wave.inputs['Scale'].default_value = 2.0
w_wave.inputs['Distortion'].default_value = 10.0
w_wave.inputs['Detail'].default_value = 6.0
w_wave.inputs['Detail Scale'].default_value = 3.0

w_noise = wt.nodes.new('ShaderNodeTexNoise')
w_noise.inputs['Scale'].default_value = 60
w_noise.inputs['Detail'].default_value = 12
w_noise.inputs['Roughness'].default_value = 0.7

w_mix = wt.nodes.new('ShaderNodeMix')
w_mix.data_type = 'FLOAT'
w_mix.inputs['Factor'].default_value = 0.3

# Warmer, lighter wood tones
w_ramp = wt.nodes.new('ShaderNodeValToRGB')
w_ramp.color_ramp.elements[0].position = 0.1
w_ramp.color_ramp.elements[0].color = (0.04, 0.025, 0.014, 1.0)
mid = w_ramp.color_ramp.elements.new(0.45)
mid.color = (0.075, 0.05, 0.028, 1.0)
w_ramp.color_ramp.elements[1].position = 0.8
w_ramp.color_ramp.elements[1].color = (0.14, 0.09, 0.05, 1.0)

# Scratches
w_scratch = wt.nodes.new('ShaderNodeTexNoise')
w_scratch.inputs['Scale'].default_value = 200
w_scratch.inputs['Detail'].default_value = 15
w_scratch.inputs['Roughness'].default_value = 0.95

# Dings
w_dings = wt.nodes.new('ShaderNodeTexNoise')
w_dings.inputs['Scale'].default_value = 8
w_dings.inputs['Detail'].default_value = 3

# Bumps
w_bump = wt.nodes.new('ShaderNodeBump')
w_bump.inputs['Strength'].default_value = 0.3
w_bump.inputs['Distance'].default_value = 0.01
w_bump2 = wt.nodes.new('ShaderNodeBump')
w_bump2.inputs['Strength'].default_value = 0.15
w_bump2.inputs['Distance'].default_value = 0.02

# Connect
wt.links.new(w_coord.outputs['Object'], w_mapping.inputs['Vector'])
wt.links.new(w_mapping.outputs['Vector'], w_wave.inputs['Vector'])
wt.links.new(w_mapping.outputs['Vector'], w_noise.inputs['Vector'])
wt.links.new(w_wave.outputs['Fac'], w_mix.inputs[2])
wt.links.new(w_noise.outputs['Fac'], w_mix.inputs[3])
wt.links.new(w_mix.outputs[0], w_ramp.inputs['Fac'])
wt.links.new(w_ramp.outputs['Color'], w_bsdf.inputs['Base Color'])
wt.links.new(w_wave.outputs['Fac'], w_bump.inputs['Height'])
wt.links.new(w_dings.outputs['Fac'], w_bump2.inputs['Height'])
wt.links.new(w_bump.outputs['Normal'], w_bump2.inputs['Normal'])
wt.links.new(w_bump2.outputs['Normal'], w_bsdf.inputs['Normal'])
wt.links.new(w_bsdf.outputs['BSDF'], w_out.inputs['Surface'])
wood.data.materials.append(mat_wood)

# ============================================================
# COMPACT LAYOUT
# ============================================================
# Title: y=8 to y=72 (tight at top)
# Row 1 labels: y=78
# Row 1 knobs: y=92 to y=154 (62px knobs)
# Row 2 labels: y=172
# Row 2 knobs: y=186 to y=248
# Row 3 labels: y=266
# Row 3 knobs: y=280 to y=342
# Portrait: bottom-right, y=360 to y=560 (200x200 square)
# Total active height: ~560px out of 620

# TITLE
tcx, tcy = gui_to_scene(510, 40)
make_textured_plane('NeonTitle', NEON_TITLE_PATH,
    tcx, tcy, 0.02, 3.4, 0.38, emission=14.0)

tbw, tbh = 1.82, 0.24
make_neon_tube('TitleBorder', [
    (-tbw, tcy - tbh, 0.025),
    (tbw, tcy - tbh, 0.025),
    (tbw, tcy + tbh, 0.025),
    (-tbw, tcy + tbh, 0.025),
    (-tbw, tcy - tbh, 0.025),
], radius=0.02, strength=18.0)

# LABELS (compact -- right above knob zones)
labels_info = [
    ('SWELL',  130, 80),     # left, row 1
    ('VINYL',  130, 175),    # left, row 2
    ('MASTER', 130, 270),    # left, row 3
    ('PSYCHE', 560, 80),     # right, row 1
    ('LFO',    560, 175),    # right, row 2
]

for name, gx, gy in labels_info:
    lx, ly = gui_to_scene(gx, gy)
    make_textured_plane(f'Label_{name}',
        f'/tmp/aether-art/crayon_{name.lower()}_v2.png',
        lx, ly, 0.005, 0.6, 0.14, emission=3.0)

# PORTRAIT (bottom-right, large, fills frame)
# 200x200px square, bottom-right corner
pcx, pcy = gui_to_scene(900, 460)
ps = 1.0  # scene units -- big and prominent

make_textured_plane('AustinPortrait', PORTRAIT_PATH,
    pcx, pcy, 0.01, ps, ps, emission=0, roughness=0.3)

# Neon border flush around portrait
tr = 0.018
hw = ps / 2 + tr
make_neon_tube('PortraitBorder', [
    (pcx - hw, pcy - hw, 0.02),
    (pcx + hw, pcy - hw, 0.02),
    (pcx + hw, pcy + hw, 0.02),
    (pcx - hw, pcy + hw, 0.02),
    (pcx - hw, pcy - hw, 0.02),
], radius=0.018, strength=15.0)

# OUTER NEON BORDER
obw, obh = 2.48, 1.50
make_neon_tube('OuterBorder', [
    (-obw, -obh, 0.015),
    (obw, -obh, 0.015),
    (obw, obh, 0.015),
    (-obw, obh, 0.015),
    (-obw, -obh, 0.015),
], radius=0.012, strength=6.0, color=(1.0, 0.04, 0.01, 1.0))

# ============================================================
# LIGHTING
# ============================================================
bpy.ops.object.light_add(type='AREA', location=(0, 0, 4))
fill = bpy.context.active_object
fill.data.energy = 20
fill.data.size = 8.0
fill.data.color = (0.95, 0.88, 0.82)

bpy.ops.object.light_add(type='SPOT', location=(pcx, pcy, 2.5))
spot = bpy.context.active_object
spot.data.energy = 30
spot.data.spot_size = math.radians(28)
spot.data.spot_blend = 0.5

# ============================================================
# RENDER
# ============================================================
scene.render.filepath = OUTPUT_PATH
bpy.ops.render.render(write_still=True)
print(f"DONE: Secret Sauce v4 rendered to {OUTPUT_PATH}")
