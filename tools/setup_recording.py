"""Prepare an isolated Blender scene for a real UI recording."""
import bpy
import sys
from pathlib import Path
from mathutils import Quaternion

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
import addon_utils
addon_utils.enable('kuanfu_outliner_focus', default_set=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for col in list(bpy.data.collections):
    bpy.data.collections.remove(col)

for name, x, kind, color in [('Ring',-3,'TORUS',(.23,.48,.7,1)),('Sphere',0,'SPHERE',(.6,.36,.2,1)),('Cube',3,'CUBE',(.32,.55,.4,1))]:
    group = bpy.data.collections.new(name+' Collection')
    bpy.context.scene.collection.children.link(group)
    sub = bpy.data.collections.new(name+' Geometry')
    group.children.link(sub)
    if kind=='TORUS':
        bpy.ops.mesh.primitive_torus_add(major_radius=.85,minor_radius=.25,location=(x,0,0),rotation=(1.1,.2,0))
    elif kind=='SPHERE':
        bpy.ops.mesh.primitive_uv_sphere_add(segments=48,ring_count=24,location=(x,0,0))
    else:
        bpy.ops.mesh.primitive_cube_add(size=1.7,location=(x,0,0),rotation=(.15,.2,.2))
        bevel=bpy.context.object.modifiers.new('Rounded edges','BEVEL')
        bevel.width=.15
        bevel.segments=5
    ob=bpy.context.object
    ob.name=name
    ob.color=color
    for col in list(ob.users_collection):
        col.objects.unlink(ob)
    sub.objects.link(ob)
    for face in ob.data.polygons:
        face.use_smooth=True
bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active=None
bpy.context.preferences.view.show_splash=False
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            space=area.spaces.active
            space.show_region_ui=False
            space.show_region_toolbar=False
            space.overlay.show_floor=False
            space.overlay.show_axis_x=False
            space.overlay.show_axis_y=False
            space.overlay.show_cursor=False
            space.shading.type='SOLID'
            space.shading.color_type='OBJECT'
            space.shading.light='STUDIO'
            space.region_3d.view_distance=13
            space.region_3d.view_location=(0,0,0)
            space.region_3d.view_rotation=Quaternion((1,0,0),1.22)
            space.region_3d.view_perspective='ORTHO'
        elif area.type=='OUTLINER':
            area.spaces.active.use_sync_select=True

bpy.ops.wm.save_as_mainfile(filepath=str(root/'work'/'Kuanfu Outliner Demo.blend'))
