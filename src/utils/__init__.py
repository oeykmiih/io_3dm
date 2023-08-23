# SPDX-License-Identifier: GPL-2.0-or-later
__version__ = '0.1.0'
import bpy

from . import blcol
from . import blop
from . import blpy
from .log import (
    log,
    verb,
    debug,
)
from .std import (
    rsetattr,
    rgetattr,
)

CLASSES = [
    blop.UTILS_OT_Select,
    blop.UTILS_OT_Nothing
]

def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    return None

def unregister():
    for cls in CLASSES:
        bpy.utils.unregister_class(cls)
    return None
