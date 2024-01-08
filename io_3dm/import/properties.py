# SPDX-License-Identifier: GPL-2.0-or-later
import bpy

from io_3dm import utils
addon = utils.bpy.Addon()

class IO3DM_hash(bpy.types.PropertyGroup):
    blob : bpy.props.PointerProperty(
        name = "Data",
        type = bpy.types.Object,
    )

class Collection(bpy.types.PropertyGroup):
    project : bpy.props.BoolProperty()
    col_idx : bpy.props.IntProperty(
        name = "Data Collection Index"
    )
    col_0 : bpy.props.CollectionProperty(
        name = "Data Collection 1",
        type = IO3DM_hash,
    )
    col_1 : bpy.props.CollectionProperty(
        name = "Data Collection 2",
        type = IO3DM_hash,
    )

CLASSES = [
    IO3DM_hash,
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