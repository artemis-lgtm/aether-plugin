"""
Austin's Secret Sauce — Photorealistic 3D guitar pedal v6.
Adds: 3D knobs on pedal surface, footswitch, I/O jacks, refined materials.
"""

import bpy
import bmesh
import math
from mathutils import Vector

OUTPUT_PATH = '/tmp/aether-art/secret_sauce_v11.png'
FACE_ART = '/tmp/aether-art/pedal_face_v11.png'
HDRI_PATH = '/tmp/aether-art/outdoor.hdr'

RENDER_W = 1020
RENDER_H = 620

# ============================================================
# SCENE
# ============================================================
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 200
scene.render.resolution_x = RENDER_W
scene.render.resolution_y = RENDER_H
scene.render.film_transparent = False
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.view_settings.view_transform = 'Filmic'
scene.view_settings.look = 'Medium High Contrast'
scene.view_settings.exposure = -0.2

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
env_tex.image = bpy.data.images.load(HDRI_PATH)
bg = wn.new('ShaderNodeBackground')
bg.inputs['Strength'].default_value = 1.5
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
bpy.ops.mesh.bevel(offset=0.12, segments=5, affect='EDGES')
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.shade_smooth()

# --- MATERIALS ---
# Top face: artwork
mat_top = bpy.data.materials.new('PedalTop')
mat_top.use_nodes = True
nt = mat_top.node_tree
nt.nodes.clear()
t_out = nt.nodes.new('ShaderNodeOutputMaterial')
t_bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
t_bsdf.inputs['Roughness'].default_value = 0.65  # matte powder coat finish
t_bsdf.inputs['Coat Weight'].default_value = 0.0   # NO clearcoat -- matte surface
t_bsdf.inputs['Coat Roughness'].default_value = 1.0
t_tex = nt.nodes.new('ShaderNodeTexImage')
t_tex.image = bpy.data.images.load(FACE_ART)
t_tex.interpolation = 'Smart'
nt.links.new(t_tex.outputs['Color'], t_bsdf.inputs['Base Color'])
nt.links.new(t_bsdf.outputs['BSDF'], t_out.inputs['Surface'])

# Side: bright aluminum
mat_side = bpy.data.materials.new('PedalSide')
mat_side.use_nodes = True
ns = mat_side.node_tree
ns.nodes.clear()
s_out = ns.nodes.new('ShaderNodeOutputMaterial')
s_bsdf = ns.nodes.new('ShaderNodeBsdfPrincipled')
s_bsdf.inputs['Base Color'].default_value = (0.6, 0.58, 0.55, 1.0)
s_bsdf.inputs['Metallic'].default_value = 1.0
s_bsdf.inputs['Roughness'].default_value = 0.2
s_bsdf.inputs['Anisotropic'].default_value = 0.3
ns.links.new(s_bsdf.outputs['BSDF'], s_out.inputs['Surface'])

# Bottom: dark
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
# SHARED MATERIALS
# ============================================================
def make_chrome_mat(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = (0.7, 0.68, 0.65, 1.0)
    bsdf.inputs['Metallic'].default_value = 1.0
    bsdf.inputs['Roughness'].default_value = 0.1
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat

def make_white_plastic_mat(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = (0.92, 0.90, 0.88, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.35
    bsdf.inputs['Specular IOR Level'].default_value = 0.5
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
# 3D KNOBS on pedal surface
# ============================================================
# Knob positions in pedal-face UV coords (0-1 range -> pedal coords)
# From the face artwork layout:
# Left col: Swell(3 knobs), Vinyl(2), Master(2)
# Right col: Psyche(7 knobs), LFO(5)

def uv_to_pedal(u, v):
    """Convert UV coords (0-1, from top-left) to pedal surface coords."""
    x = (u - 0.5) * pedal_w
    y = (0.5 - v) * pedal_d  # V inverted (top of image = front of pedal)
    return (x, y, pedal_h + 0.001)  # slightly above pedal surface

def make_knob(name, u, v, radius=0.08, height=0.07):
    """Create a chunky white knob with black indicator on pedal surface."""
    x, y, z = uv_to_pedal(u, v)
    
    # Knob body (cylinder)
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height,
        location=(x, y, z + height/2))
    knob = bpy.context.active_object
    knob.name = name
    bpy.ops.object.shade_smooth()
    knob.data.materials.append(mat_white)
    
    # Knob cap (slightly domed -- smaller cylinder on top)
    bpy.ops.mesh.primitive_cylinder_add(radius=radius*0.9, depth=0.01,
        location=(x, y, z + height + 0.005))
    cap = bpy.context.active_object
    cap.name = name + '_cap'
    bpy.ops.object.shade_smooth()
    cap.data.materials.append(mat_white)
    
    # Indicator line (thin black box on top)
    bpy.ops.mesh.primitive_cube_add(size=1,
        location=(x, y + radius*0.35, z + height + 0.012))
    ind = bpy.context.active_object
    ind.name = name + '_ind'
    ind.scale = (radius*0.12, radius*0.7, 0.005)
    bpy.ops.object.transform_apply(scale=True)
    ind.data.materials.append(mat_indicator)
    
    # Chrome skirt ring (torus at base)
    bpy.ops.mesh.primitive_torus_add(
        major_radius=radius + 0.01, minor_radius=0.008,
        location=(x, y, z + 0.005))
    ring = bpy.context.active_object
    ring.name = name + '_ring'
    bpy.ops.object.shade_smooth()
    ring.data.materials.append(mat_chrome)
    
    return knob

# Knob positions -- VERIFIED clearances against face artwork v7
# Every knob top edge is 17+ px below its section label bottom edge

swell_knobs = [
    ('Swell_Sens',    80/1020, 240/620),
    ('Swell_Attack', 160/1020, 240/620),
    ('Swell_Depth',  240/1020, 240/620),
]

vinyl_knobs = [
    ('Vinyl_Year',    80/1020, 355/620),
    ('Vinyl_Detune', 160/1020, 355/620),
]

master_knobs = [
    ('Master_Mix',    80/1020, 465/620),
    ('Master_Gain',  160/1020, 465/620),
]

psyche_knobs = [
    ('Psyche_Shimmer', 455/1020, 240/620),
    ('Psyche_Space',   535/1020, 240/620),
    ('Psyche_Mod',     615/1020, 240/620),
    ('Psyche_Warp',    695/1020, 240/620),
    ('Psyche_Mix',     455/1020, 295/620),
    ('Psyche_Notch',   535/1020, 295/620),
    ('Psyche_Sweep',   615/1020, 295/620),
]

lfo_knobs = [
    ('LFO_Shape', 455/1020, 410/620),
    ('LFO_Rate',  535/1020, 410/620),
    ('LFO_Depth', 615/1020, 410/620),
    ('LFO_Div',   455/1020, 485/620),
    ('LFO_Phase', 535/1020, 485/620),
]

all_knobs = swell_knobs + vinyl_knobs + master_knobs + psyche_knobs + lfo_knobs

for name, u, v in all_knobs:
    make_knob(name, u, v, radius=0.07, height=0.06)

# ============================================================
# FOOTSWITCH (center bottom)
# ============================================================
fs_x, fs_y, fs_z = uv_to_pedal(0.35, 0.88)

# Switch housing
bpy.ops.mesh.primitive_cylinder_add(radius=0.06, depth=0.04,
    location=(fs_x, fs_y, fs_z + 0.02))
fswitch = bpy.context.active_object
fswitch.name = 'Footswitch'
bpy.ops.object.shade_smooth()
fswitch.data.materials.append(mat_chrome)

# Switch button (rubber cap)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.04, segments=16, ring_count=8,
    location=(fs_x, fs_y, fs_z + 0.045))
fbtn = bpy.context.active_object
fbtn.name = 'FootswitchBtn'
fbtn.scale = (1, 1, 0.5)
bpy.ops.object.transform_apply(scale=True)
bpy.ops.object.shade_smooth()

mat_rubber = bpy.data.materials.new('Rubber')
mat_rubber.use_nodes = True
rnt = mat_rubber.node_tree
rnt.nodes.clear()
r_out = rnt.nodes.new('ShaderNodeOutputMaterial')
r_bsdf = rnt.nodes.new('ShaderNodeBsdfPrincipled')
r_bsdf.inputs['Base Color'].default_value = (0.03, 0.03, 0.03, 1.0)
r_bsdf.inputs['Roughness'].default_value = 0.8
rnt.links.new(r_bsdf.outputs['BSDF'], r_out.inputs['Surface'])
fbtn.data.materials.append(mat_rubber)

# ============================================================
# SCREWS (4 corners)
# ============================================================
inset_x = pedal_w/2 - 0.15
inset_y = pedal_d/2 - 0.12
for sx, sy, sn in [(-inset_x, inset_y, 'TL'), (inset_x, inset_y, 'TR'),
                    (-inset_x, -inset_y, 'BL'), (inset_x, -inset_y, 'BR')]:
    bpy.ops.mesh.primitive_cylinder_add(radius=0.035, depth=0.015,
        location=(sx, sy, pedal_h + 0.003))
    s = bpy.context.active_object
    s.name = f'Screw_{sn}'
    bpy.ops.object.shade_smooth()
    s.data.materials.append(mat_chrome)

# ============================================================
# LED indicator (near footswitch)
# ============================================================
led_x, led_y = fs_x + 0.15, fs_y
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.015, location=(led_x, led_y, pedal_h + 0.01))
led = bpy.context.active_object
led.name = 'LED'
bpy.ops.object.shade_smooth()

mat_led = bpy.data.materials.new('LED')
mat_led.use_nodes = True
lnt = mat_led.node_tree
lnt.nodes.clear()
l_out = lnt.nodes.new('ShaderNodeOutputMaterial')
l_emit = lnt.nodes.new('ShaderNodeEmission')
l_emit.inputs['Color'].default_value = (1.0, 0.05, 0.02, 1.0)  # red LED
l_emit.inputs['Strength'].default_value = 8.0
lnt.links.new(l_emit.outputs['Emission'], l_out.inputs['Surface'])
led.data.materials.append(mat_led)

# ============================================================
# SURFACE
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
f_bsdf.inputs['Base Color'].default_value = (0.18, 0.17, 0.17, 1.0)  # mid-gray felt
f_bsdf.inputs['Roughness'].default_value = 0.95  # matte felt surface
nf.links.new(f_bsdf.outputs['BSDF'], f_out.inputs['Surface'])
surface.data.materials.append(mat_surf)

# ============================================================
# CAMERA
# ============================================================
cam_angle = math.radians(10)
cam_dist = 7.5
cam_x = 0
cam_y = -cam_dist * math.sin(cam_angle)
cam_z = cam_dist * math.cos(cam_angle)

bpy.ops.object.camera_add(location=(cam_x, cam_y, cam_z))
camera = bpy.context.active_object
camera.data.type = 'PERSP'
camera.data.lens = 50

direction = Vector((0, 0, pedal_h/2)) - Vector((cam_x, cam_y, cam_z))
camera.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = camera

# ============================================================
# LIGHTING
# ============================================================
# Soft key light (large area, diffused -- like indoor window light)
bpy.ops.object.light_add(type='AREA', location=(0.3, -0.5, 5))
key = bpy.context.active_object
key.data.energy = 120
key.data.size = 6.0  # very large = very soft shadows
key.data.color = (1.0, 0.98, 0.95)
key.rotation_euler = (math.radians(5), 0, 0)

# Soft fill (almost ambient)
bpy.ops.object.light_add(type='AREA', location=(-2, 0, 4))
fill = bpy.context.active_object
fill.data.energy = 50
fill.data.size = 6.0
fill.data.color = (0.95, 0.95, 0.98)

# Gentle rim (subtle edge definition)
bpy.ops.object.light_add(type='AREA', location=(0, 2, 2.5))
rim = bpy.context.active_object
rim.data.energy = 40
rim.data.size = 4.0
rim.rotation_euler = (math.radians(-30), 0, 0)

# ============================================================
# RENDER
# ============================================================
scene.render.filepath = OUTPUT_PATH
bpy.ops.render.render(write_still=True)
print(f"DONE: Pedal v6 rendered to {OUTPUT_PATH}")
