# SPDX-License-Identifier: GPL-2.0-or-later
import bpy

from . import addon
from . import utils

class IO3DM_Preferences(bpy.types.AddonPreferences):
    """Store options"""
    bl_idname = addon.name

    bool: bpy.props.BoolProperty(
        name="bool",
        default=False,
    )

    def draw(self, context):
        layout = self.layout
        return None

class IO3DM_PROPS_WindowManager(bpy.types.PropertyGroup):
    """Store state"""
    pass

CLASSES = [
    IO3DM_Preferences,
    IO3DM_PROPS_WindowManager,
]

def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)

    addon.set_props(IO3DM_PROPS_WindowManager)
    return None

def unregister():
    addon.del_props(IO3DM_PROPS_WindowManager)

    for cls in CLASSES:
        bpy.utils.unregister_class(cls)
    return None
