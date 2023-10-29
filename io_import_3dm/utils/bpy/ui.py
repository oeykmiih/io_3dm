# SPDX-License-Identifier: GPL-2.0-or-later
import bpy

from . import ops

def label(layout, text="", depress=False, align=True):
    widget = layout.row(align=align)
    widget.operator(
        ops.UTILS_OT_Placeholder.bl_idname,
        text=text,
        depress=depress,
    )
    return widget

def alert(layout, text="", align=True):
    widget = layout.column(align=align)
    widget.alert = True
    widget.operator(
        ops.UTILS_OT_Placeholder.bl_idname,
        text=text,
    )
    return widget
