# SPDX-License-Identifier: GPL-2.0-or-later
bl_info = {
    "name": "Import Rhinoceros 3D",
    "author": "Nathan 'jesterKing' Letwory, Joel Putnam, Tom Svilans, Lukas Fertig, joao baptista",
    "blender": (3, 3, 0),
    "version": (0, 3, 0),
    "location": "File > Import > Rhinoceros 3D (.3dm)",
    "description": "This addon lets you import Rhinoceros 3dm files",
    "warning": "The importer doesn't handle all data in 3dm files yet",
    "wiki_url": "",
    "category": "Import-Export",
}
__version__ = "0.3.0-231102"
__prefix__ = "IO3DM"

from io_import_3dm import utils
addon = utils.bpy.Addon()

LIBRARIES = {
    "rhino" : None,
}
LIBRARIES = utils.import_libraries(LIBRARIES)

MODULES = {
    "export" : None,
    "import" : None,
}

MODULES = utils.import_modules(MODULES)
import bpy

@addon.property
class Preferences(bpy.types.AddonPreferences):
    bl_idname = addon.name

    items = (name for name, module in MODULES.items() if hasattr(module, "UI"))

    ui_prefs_tab: bpy.props.EnumProperty(
        name = "ui_prefs_tab",
        description = "",
        items = utils.bpy.enum_from_list(items, raw=True),
    )

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        # col.row().prop(self, "ui_prefs_tab", expand=True)
        # properties = getattr(self, self.ui_prefs_tab)
        # MODULES[self.ui_prefs_tab].UI(properties, layout)
        return None

@addon.property
class WindowManager(bpy.types.PropertyGroup):
    pass

@addon.property
class Scene(bpy.types.PropertyGroup):
    pass

PROPS = [
    Preferences,
    WindowManager,
    Scene,
]


def register():
    utils.bpy.register_modules(MODULES)
    utils.bpy.register_classes(PROPS)
    addon.set_properties(PROPS)
    return None

def unregister():
    utils.bpy.unregister_classes(PROPS)
    utils.bpy.unregister_modules(MODULES)
    utils.cleanse_globals()
    return None
