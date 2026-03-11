"""
Render colored dome knob filmstrips (Pretty Princess style).
One filmstrip per section color: 128 frames, each frame is the knob rotated.
Output: horizontal strip of 128 frames.
"""
import bpy
import bmesh
import math
from mathutils import Vector

# Section colors (matching the 3D render)
SECTION_COLORS = {
    'swell':  (0.92, 0.35, 0.25),   # warm red
    'vinyl':  (0.30, 0.78, 0.50),   # green
    'master': (0.65, 0.28, 0.78),   # purple
    'psyche': (0.35, 0.60, 0.92),   # blue
    'lfo':    (0.90, 0.72, 0.25),   # gold
}

FRAME_SIZE = 128
NUM_FRAMES = 128

for section_name, color_rgb in SECTION_COLORS.items():
    print(f"Rendering {section_name} filmstrip...")
    
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 256
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = 'OPENIMAGEDENOISE'
    scene.render.resolution_x = FRAME_SIZE
    scene.render.resolution_y = FRAME_SIZE
    scene.render.film_transparent = True  # transparent background
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    
    # World: subtle studio lighting
    world = bpy.data.worlds.new('KnobWorld')
    scene.world = world
    world.use_nodes = True
    wn = world.node_tree
    wn.nodes.clear()
    bg = wn.nodes.new('ShaderNodeBackground')
    bg.inputs['Color'].default_value = (0.15, 0.14, 0.13, 1.0)
    bg.inputs['Strength'].default_value = 0.3
    out_w = wn.nodes.new('ShaderNodeOutputWorld')
    wn.links.new(bg.outputs['Background'], out_w.inputs['Surface'])
    
    # Colored plastic material
    mat = bpy.data.materials.new(f'Plastic_{section_name}')
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = (*color_rgb, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.28
    bsdf.inputs['Specular IOR Level'].default_value = 0.55
    bsdf.inputs['Subsurface Weight'].default_value = 0.18
    bsdf.inputs['Subsurface Radius'].default_value = (0.8, 0.6, 0.4)
    bsdf.inputs['Subsurface Scale'].default_value = 0.025
    noise = nt.nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 500.0
    noise.inputs['Detail'].default_value = 5.0
    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.02
    bump.inputs['Distance'].default_value = 0.001
    nt.links.new(noise.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    
    # Indicator slot material (dark)
    mat_ind = bpy.data.materials.new(f'Indicator_{section_name}')
    mat_ind.use_nodes = True
    nt2 = mat_ind.node_tree
    nt2.nodes.clear()
    out2 = nt2.nodes.new('ShaderNodeOutputMaterial')
    bsdf2 = nt2.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf2.inputs['Base Color'].default_value = (0.02, 0.02, 0.02, 1.0)
    bsdf2.inputs['Roughness'].default_value = 0.9
    nt2.links.new(bsdf2.outputs['BSDF'], out2.inputs['Surface'])
    
    # Build knob geometry
    radius = 0.45
    height = 0.32
    
    # Body cylinder
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=radius, depth=height,
        location=(0, 0, height/2))
    knob = bpy.context.active_object
    knob.name = 'KnobBody'
    bpy.ops.object.shade_smooth()
    knob.data.materials.append(mat)
    
    # Dome top
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24,
        radius=radius * 0.95, location=(0, 0, height))
    dome = bpy.context.active_object
    dome.name = 'KnobDome'
    dome.scale = (1.0, 1.0, 0.28)
    bpy.ops.object.transform_apply(scale=True)
    bpy.ops.object.shade_smooth()
    dome.data.materials.append(mat)
    
    # Slot indicator
    slot_len = radius * 0.48
    bpy.ops.mesh.primitive_cube_add(size=1,
        location=(0, slot_len/2 + 0.002, height + radius * 0.18))
    slot = bpy.context.active_object
    slot.name = 'KnobSlot'
    slot.scale = (0.025, slot_len, 0.02)
    bpy.ops.object.transform_apply(scale=True)
    slot.data.materials.append(mat_ind)
    
    # Parent all to empty for rotation
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
    pivot = bpy.context.active_object
    pivot.name = 'KnobPivot'
    
    for obj_name in ['KnobBody', 'KnobDome', 'KnobSlot']:
        bpy.data.objects[obj_name].parent = pivot
    
    # Camera: top-down with slight angle
    cam_z = 3.0
    bpy.ops.object.camera_add(location=(0, -0.2, cam_z))
    camera = bpy.context.active_object
    direction = Vector((0, 0, height/2)) - Vector((0, -0.2, cam_z))
    camera.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    camera.data.type = 'PERSP'
    camera.data.lens = 85
    scene.camera = camera
    
    # Lighting
    bpy.ops.object.light_add(type='AREA', location=(0.5, -0.8, 2.5))
    key = bpy.context.active_object
    key.data.energy = 30
    key.data.size = 2.0
    
    bpy.ops.object.light_add(type='AREA', location=(-0.8, 0.5, 2.0))
    fill = bpy.context.active_object
    fill.data.energy = 15
    fill.data.size = 1.5
    
    bpy.ops.object.light_add(type='AREA', location=(0, 1.0, 1.5))
    rim = bpy.context.active_object
    rim.data.energy = 10
    rim.data.size = 1.0
    
    # Render 128 frames
    import os
    frame_dir = f'/tmp/aether-art/knob-frames-{section_name}'
    os.makedirs(frame_dir, exist_ok=True)
    
    for i in range(NUM_FRAMES):
        angle = (i / NUM_FRAMES) * 2 * math.pi * 0.83 + math.pi * 0.58  # 300 degree sweep
        pivot.rotation_euler = (0, 0, angle)
        bpy.context.view_layer.update()
        scene.render.filepath = f'{frame_dir}/frame_{i:03d}.png'
        bpy.ops.render.render(write_still=True)
    
    print(f"  Done: {section_name} ({NUM_FRAMES} frames)")

print("All filmstrips rendered!")
