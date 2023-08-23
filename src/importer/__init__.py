# SPDX-License-Identifier: GPL-2.0-or-later
import importlib

import bpy

from . import importer
from . import converters
from . import operators

CLASSES = [
    operators.IO3DM_ImportOptions,
    importer.IO3DM_PROPS_Project,
    operators.IO3DM_OT_Load,
]

def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_file_import.append(operators.IO3DM_BT_Import)
    return None

def unregister():
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)

    bpy.types.TOPBAR_MT_file_import.remove(operators.IO3DM_BT_Import)
    return None
