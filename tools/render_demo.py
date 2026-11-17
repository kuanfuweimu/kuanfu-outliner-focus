"""Render the isolated demo scene with Blender --background --factory-startup."""
import bpy
from mathutils import Vector
from pathlib import Path

root = Path(__file__).resolve().parents[1]
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 24
scene.cycles.use_denoising = True
scene.render.resolution_x = 840
scene.render.resolution_y = 480
scene.render.resolution_percentage = 100
scene.render.film_transparent = True
scene.view_settings.view_transform = 'Standard'

def material(name, color, metallic):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Metallic'].default_value = metallic
    p.inputs['Roughness'].default_value = .24
    return m

silver = material('Satin silver', (.52, .6, .7), .65)
bpy.ops.mesh.primitive_torus_add(major_radius=.83, minor_radius=.23, location=(-2.7, 0, 0), rotation=(.9, .4, .1))
ring = bpy.context.object
ring.name = 'Ring'
bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=.94, location=(0, 0, 0))
sphere = bpy.context.object
sphere.name = 'Sphere'
bpy.ops.mesh.primitive_cube_add(size=1.6, location=(2.7, 0, 0), rotation=(.15, .15, .25))
cube = bpy.context.object
cube.name = 'Cube'
bevel = cube.modifiers.new('Soft edges', 'BEVEL')
bevel.width = .18
bevel.segments = 6
cube.modifiers.new('Weighted normals', 'WEIGHTED_NORMAL')
for ob in (ring, sphere, cube):
    ob.data.materials.append(silver)
    for p in ob.data.polygons:
        p.use_smooth = True

world = scene.world
world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (.18, .21, .28, 1)
world.node_tree.nodes['Background'].inputs[1].default_value = .5
for location, energy, size in [((-3,-4,6),1500,5),((4,1,4),2000,4),((0,4,0),1100,3)]:
    bpy.ops.object.light_add(type='AREA', location=location)
    light = bpy.context.object
    light.data.energy = energy
    light.data.shape = 'DISK'
    light.data.size = size
    light.rotation_euler = (Vector((0,0,0))-light.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(0,-12,6))
camera = bpy.context.object
camera.rotation_euler = (-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 9.6
scene.camera = camera
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = str(root / 'work' / 'models.png')
bpy.ops.render.render(write_still=True)
