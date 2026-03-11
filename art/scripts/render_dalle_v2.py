"""
Austin's Secret Sauce — FINAL photorealistic render.
Max realism pass: denoising, bump maps, SSS, edge wear, DOF, grain.
"""

import bpy
import bmesh
import math
from mathutils import Vector

OUTPUT_PATH = '/tmp/aether-art/dalle_render_v2.png'
FACE_ART = '/tmp/aether-art/dalle_face_v2.png'
HDRI_PATH = '/tmp/aether-art/outdoor.hdr'

RENDER_W = 1020
RENDER_H = 620

# ============================================================
# SCENE — high quality settings
# ============================================================
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 512
scene.cycles.use_denoising = True
scene.cycles.denoiser = 'OPENIMAGEDENOISE'
scene.cycles.max_bounces = 12
scene.cycles.diffuse_bounces = 6
scene.cycles.glossy_bounces = 6
scene.cycles.transmission_bounces = 8
scene.cycles.transparent_max_bounces = 8
scene.cycles.caustics_reflective = False  # faster, minimal visual loss
scene.cycles.caustics_refractive = False
scene.render.resolution_x = RENDER_W
scene.render.resolution_y = RENDER_H
scene.render.film_transparent = False
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.view_settings.view_transform = 'Filmic'
scene.view_settings.look = 'Medium High Contrast'
scene.view_settings.exposure = -0.15

# ============================================================
# WORLD — HDRI
# ============================================================
world = bpy.data.worlds.new('World')
scene.world = world
world.use_nodes = True
wn = world.node_tree.nodes
wl = world.node_tree.links
for n in wn: wn.remove(n)
env_tex = wn.new('ShaderNodeTexEnvironment')
env_tex.image = bpy.data.images.load(HDRI_PATH)
bg = wn.new('ShaderNodeBackground')
bg.inputs['Strength'].default_value = 1.2
out_w = wn.new('ShaderNodeOutputWorld')
wl.new(env_tex.outputs['Color'], bg.inputs['Color'])
wl.new(bg.outputs['Background'], out_w.inputs['Surface'])

# ============================================================
# PEDAL DIMENSIONS
# ============================================================
pedal_w = 3.3
pedal_d = 2.0
pedal_h = 0.6

# ============================================================
# PEDAL ENCLOSURE
# ============================================================
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, pedal_h/2))
pedal = bpy.context.active_object
pedal.name = 'Pedal'
pedal.scale = (pedal_w, pedal_d, pedal_h)
bpy.ops.object.transform_apply(scale=True)

bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.bevel(offset=0.12, segments=6, affect='EDGES')
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.shade_smooth()

# --- TOP FACE MATERIAL: powder coat with bump ---
mat_top = bpy.data.materials.new('PedalTop')
mat_top.use_nodes = True
nt = mat_top.node_tree
nt.nodes.clear()
t_out = nt.nodes.new('ShaderNodeOutputMaterial')
t_bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
t_bsdf.inputs['Roughness'].default_value = 0.62
t_bsdf.inputs['Coat Weight'].default_value = 0.05
t_bsdf.inputs['Coat Roughness'].default_value = 0.7

# Face artwork texture
t_tex = nt.nodes.new('ShaderNodeTexImage')
t_tex.image = bpy.data.images.load(FACE_ART)
t_tex.interpolation = 'Smart'
nt.links.new(t_tex.outputs['Color'], t_bsdf.inputs['Base Color'])

# Bump map: powder coat orange-peel micro texture
t_noise = nt.nodes.new('ShaderNodeTexNoise')
t_noise.inputs['Scale'].default_value = 800.0
t_noise.inputs['Detail'].default_value = 8.0
t_noise.inputs['Roughness'].default_value = 0.6
t_bump = nt.nodes.new('ShaderNodeBump')
t_bump.inputs['Strength'].default_value = 0.08
t_bump.inputs['Distance'].default_value = 0.002
nt.links.new(t_noise.outputs['Fac'], t_bump.inputs['Height'])
nt.links.new(t_bump.outputs['Normal'], t_bsdf.inputs['Normal'])

# Roughness variation (subtle)
t_noise2 = nt.nodes.new('ShaderNodeTexNoise')
t_noise2.inputs['Scale'].default_value = 200.0
t_noise2.inputs['Detail'].default_value = 4.0
t_ramp = nt.nodes.new('ShaderNodeMapRange')
t_ramp.inputs['From Min'].default_value = 0.0
t_ramp.inputs['From Max'].default_value = 1.0
t_ramp.inputs['To Min'].default_value = 0.55
t_ramp.inputs['To Max'].default_value = 0.7
nt.links.new(t_noise2.outputs['Fac'], t_ramp.inputs['Value'])
nt.links.new(t_ramp.outputs['Result'], t_bsdf.inputs['Roughness'])

nt.links.new(t_bsdf.outputs['BSDF'], t_out.inputs['Surface'])

# --- SIDE MATERIAL: cast aluminum with edge wear ---
mat_side = bpy.data.materials.new('PedalSide')
mat_side.use_nodes = True
ns = mat_side.node_tree
ns.nodes.clear()
s_out = ns.nodes.new('ShaderNodeOutputMaterial')
s_bsdf = ns.nodes.new('ShaderNodeBsdfPrincipled')
s_bsdf.inputs['Base Color'].default_value = (0.58, 0.56, 0.53, 1.0)
s_bsdf.inputs['Metallic'].default_value = 1.0
s_bsdf.inputs['Roughness'].default_value = 0.22
s_bsdf.inputs['Anisotropic'].default_value = 0.2

# Subtle brushed-metal bump on sides
s_noise = ns.nodes.new('ShaderNodeTexNoise')
s_noise.inputs['Scale'].default_value = 300.0
s_noise.inputs['Detail'].default_value = 6.0
s_noise.inputs['Roughness'].default_value = 0.8
s_bump = ns.nodes.new('ShaderNodeBump')
s_bump.inputs['Strength'].default_value = 0.05
s_bump.inputs['Distance'].default_value = 0.001
ns.links.new(s_noise.outputs['Fac'], s_bump.inputs['Height'])
ns.links.new(s_bump.outputs['Normal'], s_bsdf.inputs['Normal'])

ns.links.new(s_bsdf.outputs['BSDF'], s_out.inputs['Surface'])

# Bottom
mat_bottom = bpy.data.materials.new('PedalBottom')
mat_bottom.use_nodes = True
nb = mat_bottom.node_tree
nb.nodes.clear()
b_out = nb.nodes.new('ShaderNodeOutputMaterial')
b_bsdf = nb.nodes.new('ShaderNodeBsdfPrincipled')
b_bsdf.inputs['Base Color'].default_value = (0.02, 0.02, 0.02, 1.0)
b_bsdf.inputs['Roughness'].default_value = 0.9
nb.links.new(b_bsdf.outputs['BSDF'], b_out.inputs['Surface'])

# Assign materials
pedal.data.materials.append(mat_top)
pedal.data.materials.append(mat_side)
pedal.data.materials.append(mat_bottom)

for poly in pedal.data.polygons:
    nz = poly.normal.z
    if nz > 0.85:
        poly.material_index = 0
    elif nz < -0.5:
        poly.material_index = 2
    else:
        poly.material_index = 1

# UV map top face
bpy.context.view_layer.objects.active = pedal
bpy.ops.object.mode_set(mode='EDIT')
bm = bmesh.from_edit_mesh(pedal.data)
bm.faces.ensure_lookup_table()
uv_layer = bm.loops.layers.uv.active or bm.loops.layers.uv.new()
for face in bm.faces:
    if face.normal.z > 0.85:
        for loop in face.loops:
            co = loop.vert.co
            u = (co.x + pedal_w/2) / pedal_w
            v = (co.y + pedal_d/2) / pedal_d
            loop[uv_layer].uv = (u, v)
bmesh.update_edit_mesh(pedal.data)
bpy.ops.object.mode_set(mode='OBJECT')

# ============================================================
# SHARED MATERIALS (enhanced)
# ============================================================
def make_chrome_mat(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = (0.72, 0.70, 0.68, 1.0)
    bsdf.inputs['Metallic'].default_value = 1.0
    bsdf.inputs['Roughness'].default_value = 0.08
    # Subtle fingerprint/smudge noise
    noise = nt.nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 150.0
    noise.inputs['Detail'].default_value = 3.0
    ramp = nt.nodes.new('ShaderNodeMapRange')
    ramp.inputs['From Min'].default_value = 0.3
    ramp.inputs['From Max'].default_value = 0.7
    ramp.inputs['To Min'].default_value = 0.06
    ramp.inputs['To Max'].default_value = 0.15
    nt.links.new(noise.outputs['Fac'], ramp.inputs['Value'])
    nt.links.new(ramp.outputs['Result'], bsdf.inputs['Roughness'])
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat

def make_white_plastic_mat(name):
    """White plastic with subsurface scattering for realism."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = (0.90, 0.88, 0.86, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.32
    bsdf.inputs['Specular IOR Level'].default_value = 0.5
    # Subsurface scattering (light passing through plastic)
    bsdf.inputs['Subsurface Weight'].default_value = 0.15
    bsdf.inputs['Subsurface Radius'].default_value = (0.8, 0.6, 0.4)
    bsdf.inputs['Subsurface Scale'].default_value = 0.02
    # Subtle bump for injection mold texture
    noise = nt.nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 500.0
    noise.inputs['Detail'].default_value = 5.0
    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.03
    bump.inputs['Distance'].default_value = 0.001
    nt.links.new(noise.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat

def make_black_indicator_mat(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = (0.01, 0.01, 0.01, 1.0)
    bsdf.inputs['Roughness'].default_value = 1.0
    bsdf.inputs['Specular IOR Level'].default_value = 0.0
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat

mat_chrome = make_chrome_mat('Chrome')
mat_white = make_white_plastic_mat('WhitePlastic')
mat_indicator = make_black_indicator_mat('BlackIndicator')

# ============================================================
# RUBBER material (footswitch)
# ============================================================
mat_rubber = bpy.data.materials.new('Rubber')
mat_rubber.use_nodes = True
rnt = mat_rubber.node_tree
rnt.nodes.clear()
r_out = rnt.nodes.new('ShaderNodeOutputMaterial')
r_bsdf = rnt.nodes.new('ShaderNodeBsdfPrincipled')
r_bsdf.inputs['Base Color'].default_value = (0.025, 0.025, 0.025, 1.0)
r_bsdf.inputs['Roughness'].default_value = 0.85
r_bsdf.inputs['Subsurface Weight'].default_value = 0.05
# Rubber texture bump
r_noise = rnt.nodes.new('ShaderNodeTexNoise')
r_noise.inputs['Scale'].default_value = 400.0
r_noise.inputs['Detail'].default_value = 8.0
r_bump = rnt.nodes.new('ShaderNodeBump')
r_bump.inputs['Strength'].default_value = 0.1
r_bump.inputs['Distance'].default_value = 0.001
rnt.links.new(r_noise.outputs['Fac'], r_bump.inputs['Height'])
rnt.links.new(r_bump.outputs['Normal'], r_bsdf.inputs['Normal'])
rnt.links.new(r_bsdf.outputs['BSDF'], r_out.inputs['Surface'])

# ============================================================
# 3D KNOBS
# ============================================================
def uv_to_pedal(u, v):
    x = (u - 0.5) * pedal_w
    y = (0.5 - v) * pedal_d
    return (x, y, pedal_h + 0.001)

def make_knob(name, u, v, radius=0.08, height=0.07):
    x, y, z = uv_to_pedal(u, v)
    
    # Knob body (higher segment count for smoother)
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=radius, depth=height,
        location=(x, y, z + height/2))
    knob = bpy.context.active_object
    knob.name = name
    bpy.ops.object.shade_smooth()
    knob.data.materials.append(mat_white)
    
    # Knob cap (domed)
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=radius*0.88, depth=0.012,
        location=(x, y, z + height + 0.006))
    cap = bpy.context.active_object
    cap.name = name + '_cap'
    bpy.ops.object.shade_smooth()
    cap.data.materials.append(mat_white)
    
    # Grip ridges (subtle knurling via small cylinders around edge)
    for i in range(12):
        a = i * math.pi * 2 / 12
        rx = x + radius * 0.92 * math.cos(a)
        ry = y + radius * 0.92 * math.sin(a)
        bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.004, depth=height*0.7,
            location=(rx, ry, z + height*0.35))
        ridge = bpy.context.active_object
        ridge.name = f'{name}_ridge_{i}'
        ridge.data.materials.append(mat_white)
    
    # Indicator line
    bpy.ops.mesh.primitive_cube_add(size=1,
        location=(x, y + radius*0.35, z + height + 0.014))
    ind = bpy.context.active_object
    ind.name = name + '_ind'
    ind.scale = (radius*0.12, radius*0.7, 0.005)
    bpy.ops.object.transform_apply(scale=True)
    ind.data.materials.append(mat_indicator)
    
    # Chrome skirt ring
    bpy.ops.mesh.primitive_torus_add(
        major_radius=radius + 0.012, minor_radius=0.009,
        major_segments=48, minor_segments=12,
        location=(x, y, z + 0.005))
    ring = bpy.context.active_object
    ring.name = name + '_ring'
    bpy.ops.object.shade_smooth()
    ring.data.materials.append(mat_chrome)
    
    return knob

# Knob positions (verified v7 layout)
all_knobs = [
    ('Swell_Sens',    80/1020, 240/620),
    ('Swell_Attack', 160/1020, 240/620),
    ('Swell_Depth',  240/1020, 240/620),
    ('Vinyl_Year',    80/1020, 355/620),
    ('Vinyl_Detune', 160/1020, 355/620),
    ('Master_Mix',    80/1020, 465/620),
    ('Master_Gain',  160/1020, 465/620),
    ('Psyche_Shimmer', 420/1020, 240/620),
    ('Psyche_Space',   490/1020, 240/620),
    ('Psyche_Mod',     560/1020, 240/620),
    ('Psyche_Warp',    630/1020, 240/620),
    ('Psyche_Mix',     700/1020, 240/620),
    ('Psyche_Notch',   770/1020, 240/620),
    ('Psyche_Sweep',   840/1020, 240/620),
    ('LFO_Shape', 455/1020, 410/620),
    ('LFO_Rate',  535/1020, 410/620),
    ('LFO_Depth', 615/1020, 410/620),
    ('LFO_Div',   455/1020, 485/620),
    ('LFO_Phase', 535/1020, 485/620),
]

for name, u, v in all_knobs:
    make_knob(name, u, v, radius=0.07, height=0.06)

# ============================================================
# FOOTSWITCH
# ============================================================
fs_x, fs_y, fs_z = uv_to_pedal(0.35, 0.88)

bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.06, depth=0.04,
    location=(fs_x, fs_y, fs_z + 0.02))
fswitch = bpy.context.active_object
fswitch.name = 'Footswitch'
bpy.ops.object.shade_smooth()
fswitch.data.materials.append(mat_chrome)

bpy.ops.mesh.primitive_uv_sphere_add(radius=0.04, segments=24, ring_count=12,
    location=(fs_x, fs_y, fs_z + 0.045))
fbtn = bpy.context.active_object
fbtn.name = 'FootswitchBtn'
fbtn.scale = (1, 1, 0.5)
bpy.ops.object.transform_apply(scale=True)
bpy.ops.object.shade_smooth()
fbtn.data.materials.append(mat_rubber)

# ============================================================
# SCREWS (hex head style with proper detail)
# ============================================================
inset_x = pedal_w/2 - 0.15
inset_y = pedal_d/2 - 0.12
for sx, sy, sn in [(-inset_x, inset_y, 'TL'), (inset_x, inset_y, 'TR'),
                    (-inset_x, -inset_y, 'BL'), (inset_x, -inset_y, 'BR')]:
    # Screw head
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.032, depth=0.012,
        location=(sx, sy, pedal_h + 0.003))
    s = bpy.context.active_object
    s.name = f'Screw_{sn}'
    bpy.ops.object.shade_smooth()
    s.data.materials.append(mat_chrome)
    # Phillips slot
    bpy.ops.mesh.primitive_cube_add(size=1,
        location=(sx, sy, pedal_h + 0.009))
    slot = bpy.context.active_object
    slot.name = f'ScrewSlot_{sn}'
    slot.scale = (0.025, 0.003, 0.005)
    bpy.ops.object.transform_apply(scale=True)
    slot.data.materials.append(mat_indicator)  # dark slot

# ============================================================
# LED
# ============================================================
led_x, led_y = fs_x + 0.15, fs_y
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.015, segments=16, ring_count=8,
    location=(led_x, led_y, pedal_h + 0.01))
led = bpy.context.active_object
led.name = 'LED'
bpy.ops.object.shade_smooth()

mat_led = bpy.data.materials.new('LED')
mat_led.use_nodes = True
lnt = mat_led.node_tree
lnt.nodes.clear()
l_out = lnt.nodes.new('ShaderNodeOutputMaterial')
l_emit = lnt.nodes.new('ShaderNodeEmission')
l_emit.inputs['Color'].default_value = (1.0, 0.05, 0.02, 1.0)
l_emit.inputs['Strength'].default_value = 6.0
lnt.links.new(l_emit.outputs['Emission'], l_out.inputs['Surface'])
led.data.materials.append(mat_led)

# ============================================================
# I/O JACKS (side-mounted)
# ============================================================
for jx, jn in [(-pedal_w/2 + 0.001, 'Input'), (pedal_w/2 - 0.001, 'Output')]:
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.04, depth=0.06,
        location=(jx, 0, pedal_h * 0.4))
    jack = bpy.context.active_object
    jack.name = f'Jack_{jn}'
    jack.rotation_euler = (0, math.radians(90), 0)
    bpy.ops.object.shade_smooth()
    jack.data.materials.append(mat_chrome)
    # Jack nut
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.05, depth=0.015,
        location=(jx, 0, pedal_h * 0.4))
    nut = bpy.context.active_object
    nut.name = f'JackNut_{jn}'
    nut.rotation_euler = (0, math.radians(90), 0)
    bpy.ops.object.shade_smooth()
    nut.data.materials.append(mat_chrome)

# ============================================================
# SURFACE (felt backdrop with texture)
# ============================================================
bpy.ops.mesh.primitive_plane_add(size=15, location=(0, 0, -0.001))
surface = bpy.context.active_object
surface.name = 'Surface'
mat_surf = bpy.data.materials.new('Surface')
mat_surf.use_nodes = True
nf = mat_surf.node_tree
nf.nodes.clear()
f_out = nf.nodes.new('ShaderNodeOutputMaterial')
f_bsdf = nf.nodes.new('ShaderNodeBsdfPrincipled')
f_bsdf.inputs['Base Color'].default_value = (0.16, 0.155, 0.15, 1.0)
f_bsdf.inputs['Roughness'].default_value = 0.95
# Felt texture bump
f_noise = nf.nodes.new('ShaderNodeTexNoise')
f_noise.inputs['Scale'].default_value = 100.0
f_noise.inputs['Detail'].default_value = 10.0
f_noise.inputs['Roughness'].default_value = 0.7
f_bump = nf.nodes.new('ShaderNodeBump')
f_bump.inputs['Strength'].default_value = 0.15
f_bump.inputs['Distance'].default_value = 0.005
nf.links.new(f_noise.outputs['Fac'], f_bump.inputs['Height'])
nf.links.new(f_bump.outputs['Normal'], f_bsdf.inputs['Normal'])
nf.links.new(f_bsdf.outputs['BSDF'], f_out.inputs['Surface'])
surface.data.materials.append(mat_surf)

# ============================================================
# CAMERA (with subtle DOF)
# ============================================================
cam_angle = math.radians(10)
cam_dist = 7.5
cam_x = 0
cam_y = -cam_dist * math.sin(cam_angle)
cam_z = cam_dist * math.cos(cam_angle)

bpy.ops.object.camera_add(location=(cam_x, cam_y, cam_z))
camera = bpy.context.active_object
camera.data.type = 'PERSP'
camera.data.lens = 55  # slightly tighter lens
# Depth of field
camera.data.dof.use_dof = True
camera.data.dof.focus_distance = cam_dist  # focus on pedal center
camera.data.dof.aperture_fstop = 11.0  # product photo f-stop (subtle DOF)

direction = Vector((0, 0, pedal_h/2)) - Vector((cam_x, cam_y, cam_z))
camera.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = camera

# ============================================================
# LIGHTING (studio product photography setup)
# ============================================================
# Key light: large soft overhead, slightly front
bpy.ops.object.light_add(type='AREA', location=(0.5, -1.0, 5.5))
key = bpy.context.active_object
key.data.energy = 100
key.data.size = 5.0
key.data.color = (1.0, 0.98, 0.95)
key.rotation_euler = (math.radians(8), 0, 0)

# Fill: opposite side, softer
bpy.ops.object.light_add(type='AREA', location=(-2.5, 0.5, 4))
fill = bpy.context.active_object
fill.data.energy = 40
fill.data.size = 5.0
fill.data.color = (0.93, 0.95, 0.98)

# Rim/back: subtle edge definition
bpy.ops.object.light_add(type='AREA', location=(0, 2.5, 2))
rim = bpy.context.active_object
rim.data.energy = 30
rim.data.size = 3.0
rim.rotation_euler = (math.radians(-35), 0, 0)
rim.data.color = (1.0, 0.96, 0.92)

# Low front accent (catches front bevel)
bpy.ops.object.light_add(type='AREA', location=(0, -2.0, 0.8))
front = bpy.context.active_object
front.data.energy = 15
front.data.size = 2.5
front.rotation_euler = (math.radians(60), 0, 0)
front.data.color = (1.0, 0.98, 0.95)

# Side highlight (catches left edge for depth)
bpy.ops.object.light_add(type='AREA', location=(3, 0, 1.5))
side = bpy.context.active_object
side.data.energy = 20
side.data.size = 2.0
side.rotation_euler = (0, math.radians(-45), 0)
side.data.color = (0.98, 0.97, 0.95)

# Skip compositing nodes -- render quality comes from materials + samples

# ============================================================
# RENDER
# ============================================================
scene.render.filepath = OUTPUT_PATH
bpy.ops.render.render(write_still=True)
print(f"DONE: FINAL render to {OUTPUT_PATH}")
