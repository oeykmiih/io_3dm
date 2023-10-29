# SPDX-License-Identifier: GPL-2.0-or-later
__version__ = '0.2.0a'
import bpy

from . import blcol
from . import blob
from .blop import (
    UTILS_OT_Select,
    UTILS_OT_Placeholder,
)
from . import blui
from . import blpy
from .log import (
    log,
    verb,
    debug,
)
from .std import (
    rgetattr,
    rsetattr,
)

CLASSES = [
    UTILS_OT_Select,
    UTILS_OT_Placeholder,
]

def register():
    for cls in CLASSES:
        if hasattr(bpy.types, cls.__name__):
            continue
        bpy.utils.register_class(cls)
    return None

def unregister():
    for cls in reversed(CLASSES):
        if not hasattr(bpy.types, cls.__name__):
            continue
        bpy.utils.unregister_class(cls)
    return None
