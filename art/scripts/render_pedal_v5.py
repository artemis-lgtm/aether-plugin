"""
Austin's Secret Sauce — Photorealistic 3D guitar pedal render.
The ENTIRE UI is a 3D pedal with artwork UV-mapped on the face.
Inspired by Turnt Plugins Pretty Pretty Princess Sparkle.
"""

import bpy
import bmesh
import math
from mathutils import Vector

OUTPUT_PATH = '/tmp/aether-art/secret_sauce_v5.png'
FACE_ART = '/tmp/aether-art/pedal_face_v2.png'
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
scene.cycles.samples = 200  # high quality
scene.render.resolution_x = RENDER_W
scene.render.resolution_y = RENDER_H
scene.render.film_transparent = False
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.view_settings.view_transform = 'Filmic'
scene.view_settings.look = 'Medium High Contrast'
scene.view_settings.exposure = -0.3

# ============================================================
# WORLD: Studio HDRI
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
# PEDAL ENCLOSURE (Hammond-style box with beveled edges)
# ============================================================
# Pedal proportions based on 1020x620 aspect = 1.645
pedal_w = 3.3   # width (x)
pedal_d = 2.0   # depth (y)
pedal_h = 0.6   # height (z) -- thicker for visible edges

bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, pedal_h/2))
pedal = bpy.context.active_object
pedal.name = 'Pedal'
pedal.scale = (pedal_w, pedal_d, pedal_h)
bpy.ops.object.transform_apply(scale=True)

# Bevel edges for rounded stompbox look
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.bevel(offset=0.12, segments=5, affect='EDGES')
bpy.ops.object.mode_set(mode='OBJECT')

# Smooth shading for proper reflections
bpy.ops.object.shade_smooth()

# ============================================================
# MATERIALS
# ============================================================

# --- Top face material: artwork UV-mapped ---
mat_top = bpy.data.materials.new('PedalTop')
mat_top.use_nodes = True
nt = mat_top.node_tree
nt.nodes.clear()

t_out = nt.nodes.new('ShaderNodeOutputMaterial')
t_bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
t_bsdf.inputs['Roughness'].default_value = 0.35  # slightly glossy printed surface
t_bsdf.inputs['Specular IOR Level'].default_value = 0.5
# Clearcoat for that "lacquered pedal" look
t_bsdf.inputs['Coat Weight'].default_value = 0.4
t_bsdf.inputs['Coat Roughness'].default_value = 0.15

t_tex = nt.nodes.new('ShaderNodeTexImage')
t_tex.image = bpy.data.images.load(FACE_ART)
t_tex.interpolation = 'Smart'

nt.links.new(t_tex.outputs['Color'], t_bsdf.inputs['Base Color'])
nt.links.new(t_bsdf.outputs['BSDF'], t_out.inputs['Surface'])

# --- Side/edge material: brushed metal ---
mat_side = bpy.data.materials.new('PedalSide')
mat_side.use_nodes = True
ns = mat_side.node_tree
ns.nodes.clear()

s_out = ns.nodes.new('ShaderNodeOutputMaterial')
s_bsdf = ns.nodes.new('ShaderNodeBsdfPrincipled')
s_bsdf.inputs['Base Color'].default_value = (0.55, 0.53, 0.50, 1.0)  # bright brushed aluminum
s_bsdf.inputs['Metallic'].default_value = 1.0
s_bsdf.inputs['Roughness'].default_value = 0.25  # brushed metal
s_bsdf.inputs['Specular IOR Level'].default_value = 0.8

# Anisotropic for brushed metal look
s_bsdf.inputs['Anisotropic'].default_value = 0.3

ns.links.new(s_bsdf.outputs['BSDF'], s_out.inputs['Surface'])

# --- Bottom material: flat dark ---
mat_bottom = bpy.data.materials.new('PedalBottom')
mat_bottom.use_nodes = True
nb = mat_bottom.node_tree
nb.nodes.clear()
b_out = nb.nodes.new('ShaderNodeOutputMaterial')
b_bsdf = nb.nodes.new('ShaderNodeBsdfPrincipled')
b_bsdf.inputs['Base Color'].default_value = (0.02, 0.02, 0.02, 1.0)
b_bsdf.inputs['Roughness'].default_value = 0.9
nb.links.new(b_bsdf.outputs['BSDF'], b_out.inputs['Surface'])

# Assign materials to faces by normal direction
pedal.data.materials.append(mat_top)     # index 0
pedal.data.materials.append(mat_side)    # index 1
pedal.data.materials.append(mat_bottom)  # index 2

mesh = pedal.data
# Blender 5.0: calc_loop_normals removed, normals are auto-calculated

for poly in mesh.polygons:
    nz = poly.normal.z
    if nz > 0.85:      # top face (including bevel transitions)
        poly.material_index = 0
    elif nz < -0.5:     # bottom face
        poly.material_index = 2
    else:                # sides/edges
        poly.material_index = 1

# ============================================================
# UV MAP for top face (project artwork onto pedal top)
# ============================================================
bpy.context.view_layer.objects.active = pedal
bpy.ops.object.mode_set(mode='EDIT')

bm = bmesh.from_edit_mesh(mesh)
bm.faces.ensure_lookup_table()

uv_layer = bm.loops.layers.uv.active or bm.loops.layers.uv.new()

# Project from top (z-axis) for top-facing faces
for face in bm.faces:
    if face.normal.z > 0.85:
        for loop in face.loops:
            co = loop.vert.co
            # Map pedal coords to 0-1 UV space
            u = (co.x + pedal_w/2) / pedal_w
            v = (co.y + pedal_d/2) / pedal_d
            loop[uv_layer].uv = (u, v)

bmesh.update_edit_mesh(mesh)
bpy.ops.object.mode_set(mode='OBJECT')

# ============================================================
# SURFACE the pedal sits on (subtle, fades to dark)
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
f_bsdf.inputs['Base Color'].default_value = (0.06, 0.055, 0.05, 1.0)  # dark but not black
f_bsdf.inputs['Roughness'].default_value = 0.8
nf.links.new(f_bsdf.outputs['BSDF'], f_out.inputs['Surface'])
surface.data.materials.append(mat_surf)

# ============================================================
# CAMERA: Slight perspective (like looking down at a pedal)
# ============================================================
# 20 degree tilt, pulled back to see edges + surface
cam_angle = math.radians(20)
cam_dist = 7.0  # far enough to frame pedal with margin
cam_x = 0
cam_y = -cam_dist * math.sin(cam_angle)
cam_z = cam_dist * math.cos(cam_angle)

bpy.ops.object.camera_add(location=(cam_x, cam_y, cam_z))
camera = bpy.context.active_object
camera.data.type = 'PERSP'
camera.data.lens = 50  # standard lens, see the whole pedal

# Point camera at pedal center
direction = Vector((0, 0, pedal_h/2)) - Vector((cam_x, cam_y, cam_z))
camera.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

scene.camera = camera

# ============================================================
# LIGHTING: Product photography setup
# ============================================================
# Key light (overhead, slightly forward) 
bpy.ops.object.light_add(type='AREA', location=(0.5, -1.5, 4))
key = bpy.context.active_object
key.name = 'Key'
key.data.energy = 150
key.data.size = 3.0
key.data.color = (1.0, 0.97, 0.93)
key.rotation_euler = (math.radians(20), 0, 0)

# Fill light (softer, from the side)
bpy.ops.object.light_add(type='AREA', location=(-3, 0, 3))
fill = bpy.context.active_object
fill.name = 'Fill'
fill.data.energy = 60
fill.data.size = 4.0
fill.data.color = (0.9, 0.92, 0.95)

# Rim/edge light (catches the pedal edges from behind)
bpy.ops.object.light_add(type='AREA', location=(0, 2.5, 2))
rim = bpy.context.active_object
rim.name = 'Rim'
rim.data.energy = 80
rim.data.size = 3.0
rim.data.color = (1.0, 0.95, 0.9)
rim.rotation_euler = (math.radians(-40), 0, 0)

# Front edge accent
bpy.ops.object.light_add(type='AREA', location=(0, -2.5, 1))
front = bpy.context.active_object
front.name = 'Front'
front.data.energy = 25
front.data.size = 2.0
front.rotation_euler = (math.radians(50), 0, 0)

# ============================================================
# SCREWS (4 corners)
# ============================================================
def make_screw(name, x, y):
    """Simple Phillips screw head on pedal surface."""
    # Screw head (flat cylinder)
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.04, depth=0.02,
        location=(x, y, pedal_h + 0.005))
    screw = bpy.context.active_object
    screw.name = name
    bpy.ops.object.shade_smooth()
    
    mat = bpy.data.materials.new(name + '_mat')
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = (0.6, 0.58, 0.55, 1.0)  # chrome
    bsdf.inputs['Metallic'].default_value = 1.0
    bsdf.inputs['Roughness'].default_value = 0.15
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    screw.data.materials.append(mat)
    return screw

# Screw positions (inset from corners)
inset_x = pedal_w/2 - 0.15
inset_y = pedal_d/2 - 0.12
make_screw('Screw_TL', -inset_x, inset_y)
make_screw('Screw_TR', inset_x, inset_y)
make_screw('Screw_BL', -inset_x, -inset_y)
make_screw('Screw_BR', inset_x, -inset_y)

# ============================================================
# RENDER
# ============================================================
scene.render.filepath = OUTPUT_PATH
bpy.ops.render.render(write_still=True)
print(f"DONE: Pedal v5 rendered to {OUTPUT_PATH}")
