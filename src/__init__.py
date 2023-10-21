# SPDX-License-Identifier: GPL-2.0-or-later
bl_info = {
    "name": "Import Rhinoceros 3D",
    "author": "Nathan 'jesterKing' Letwory, Joel Putnam, Tom Svilans, Lukas Fertig, joao baptista",
    "blender": (3, 3, 0),
    "version": (2, 0, 2),
    "location": "File > Import > Rhinoceros 3D (.3dm)",
    "description": "This addon lets you import Rhinoceros 3dm files",
    "warning": "The importer doesn't handle all data in 3dm files yet",
    "wiki_url": "",
    "category": "Import-Export",
}
__version__ = "2.0.2-231021"
__addon__ = "io_import_3dm"
__prefix__ = "IO3DM"

import importlib
import os
import site
import sys


LIBRARIES = [
    "rhino3dm",
]

if LIBRARIES:
    LIB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "libs"))
    try:
        if os.path.isdir(LIB_DIR) and LIB_DIR not in sys.path:
            sys.path.insert(0, LIB_DIR)
        for name in LIBRARIES:
            importlib.import_module(name)
    finally:
        if LIB_DIR in sys.path:
            sys.path.remove(LIB_DIR)

MODULES = {
    "properties" : None,
    "importer" : None,
    "utils" : None,
}

if "bpy" in locals():
    for name, module in MODULES.items():
        MODULES[name] = importlib.reload(f"{__package__}.{name}")
else:
    for name, module in MODULES.items():
        MODULES[name] = importlib.import_module(f"{__package__}.{name}")

import bpy

def cleanse_modules():
    """Remove all plugin modules from sys.modules, will load them again, creating an effective hit-reload soluton"""
    # https://devtalk.blender.org/t/plugin-hot-reload-by-cleaning-sys-modules/20040

    import sys
    all_modules = sys.modules
    all_modules = dict(sorted(all_modules.items(),key= lambda x:x[0])) #sort them

    for key in all_modules.keys():
        if key.startswith(__name__):
            del sys.modules[key]
    return None

def register():
    for module in MODULES.values():
        module.register()
    return None

def unregister():
    for module in reversed(MODULES.values()):
        module.unregister()
    cleanse_modules()
    return None
