# SPDX-License-Identifier: GPL-2.0-or-later
import bpy

from io_import_3dm import utils
addon = utils.bpy.Addon()

class Collection(bpy.types.PropertyGroup):
    pass

CLASSES = [
    Collection,
]

PROPS = [
    Collection,
]

def register():
    utils.bpy.register_classes(CLASSES)
    addon.set_properties(PROPS)
    return None

def unregister():
    utils.bpy.unregister_classes(CLASSES)
    return None