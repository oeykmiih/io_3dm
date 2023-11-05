# SPDX-License-Identifier: GPL-2.0-or-later
import bpy

from . import obj
from . import meta

def obt(name, force=False, parent=None, local=False, overwrite=None):
    if local:
        blcol = meta.obt(
            bpy.data.collections,
            name,
            scope = bpy.context.scene.collection.children_recursive,
            force = force,
            overwrite = overwrite,
        )
    else:
        blcol = meta.obt(bpy.data.collections, name, force=force, overwrite=overwrite)
    if parent is not None and blcol is not None and name not in parent.children:
        parent.children.link(blcol)
    return blcol

def empty(blcol, objects=False, recursive=False):
    if recursive:
        collections = [c for c in blcol.children]
        while collections:
            child = collections.pop()
            empty(child, recursive=True, objects=objects)
            blcol.children.unlink(child)
    if objects:
        objects = [o for o in blcol.objects]
        while objects:
            blcol.objects.unlink(objects.pop())
    return None
