bl_info = {
    'name': 'Kuanfu Outliner Focus',
    'author': 'Kuanfu / Codex',
    'version': (1, 0, 0),
    'blender': (4, 2, 0),
    'location': 'Outliner header and Filter popover',
    'description': 'Automatically reveal the active object in the Outliner',
    'category': 'Interface',
}

import bpy
from bpy.props import BoolProperty, FloatProperty

_seen = {}
_failures = set()
_running = False


def preferences():
    addon = bpy.context.preferences.addons.get(__name__)
    return addon.preferences if addon else None


def reset_tracking(self=None, context=None):
    _seen.clear()
    _failures.clear()


def reveal(window, area, sync_selection=True):
    region = next((r for r in area.regions if r.type == 'WINDOW'), None)
    if region is None or area.spaces.active.display_mode != 'VIEW_LAYER':
        return False
    with bpy.context.temp_override(window=window, area=area, region=region):
        if not bpy.ops.outliner.show_active.poll():
            return False
        if sync_selection:
            area.spaces.active.use_sync_select = True
        result = bpy.ops.outliner.show_active()
    return 'FINISHED' in result


def update_outliners(force=False):
    prefs = preferences()
    if not force and (prefs is None or not prefs.enabled):
        return 0
    count = 0
    live = set()
    for window in bpy.context.window_manager.windows:
        active = window.view_layer.objects.active
        if active is None:
            continue
        state = (window.scene.as_pointer(), window.view_layer.as_pointer(), active.as_pointer())
        for area in window.screen.areas:
            if area.type != 'OUTLINER':
                continue
            key = (window.as_pointer(), area.as_pointer())
            live.add(key)
            if not force and _seen.get(key) == state:
                continue
            try:
                if reveal(window, area, prefs.sync_selection if prefs else True):
                    count += 1
                _seen[key] = state
            except (RuntimeError, ReferenceError) as error:
                # Do not flood the console while a window is closing or changing editors.
                _seen[key] = state
                if key not in _failures:
                    print('Kuanfu Outliner Focus:', str(error))
                    _failures.add(key)
    for key in set(_seen) - live:
        _seen.pop(key, None)
        _failures.discard(key)
    return count


def tick():
    if not _running:
        return None
    prefs = preferences()
    try:
        if not bpy.app.background and not bpy.app.is_job_running('RENDER'):
            update_outliners()
    except (RuntimeError, ReferenceError):
        reset_tracking()
    return prefs.interval if prefs else 0.25


class KUANFU_OF_preferences(bpy.types.AddonPreferences):
    bl_idname = __name__
    enabled: BoolProperty(name='Auto Reveal Selected', default=True, update=reset_tracking,
                          description='Expand and scroll the Outliner when the active object changes')
    sync_selection: BoolProperty(name='Sync Selection', default=True, update=reset_tracking,
                                 description='Enable native selection synchronization in the Outliner')
    interval: FloatProperty(name='Update Interval', default=0.25, min=0.1, max=2.0, subtype='TIME')

    def draw(self, context):
        self.layout.prop(self, 'enabled')
        self.layout.prop(self, 'sync_selection')
        self.layout.prop(self, 'interval')
        self.layout.label(text='Only updates when the active object changes; other collections stay open.')


class KUANFU_OT_reveal_active(bpy.types.Operator):
    bl_idname = 'kuanfu.outliner_reveal_active'
    bl_label = 'Reveal Active Object in Outliner'
    bl_description = 'Expand the hierarchy and scroll to the active object'
    bl_options = {'REGISTER'}

    def execute(self, context):
        count = update_outliners(force=True)
        if not count:
            self.report({'INFO'}, 'Select an object and open an Outliner in View Layer mode')
        return {'FINISHED'}


def draw_header(self, context):
    prefs = preferences()
    if prefs and context.space_data.display_mode == 'VIEW_LAYER':
        self.layout.prop(prefs, 'enabled', text='', icon='ZOOM_SELECTED', toggle=True)


def draw_filter(self, context):
    prefs = preferences()
    if prefs and context.space_data.display_mode == 'VIEW_LAYER':
        col = self.layout.column()
        col.separator()
        col.label(text='Kuanfu Outliner Focus')
        col.prop(prefs, 'enabled')
        col.operator('kuanfu.outliner_reveal_active', icon='ZOOM_SELECTED')


_classes = (KUANFU_OF_preferences, KUANFU_OT_reveal_active)


def register():
    global _running
    for cls in _classes:
        bpy.utils.register_class(cls)
    bpy.types.OUTLINER_HT_header.append(draw_header)
    bpy.types.OUTLINER_PT_filter.append(draw_filter)
    reset_tracking()
    _running = True
    if not bpy.app.background and not bpy.app.timers.is_registered(tick):
        bpy.app.timers.register(tick, first_interval=0.5, persistent=True)


def unregister():
    global _running
    _running = False
    if bpy.app.timers.is_registered(tick):
        bpy.app.timers.unregister(tick)
    bpy.types.OUTLINER_HT_header.remove(draw_header)
    bpy.types.OUTLINER_PT_filter.remove(draw_filter)
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
    reset_tracking()
