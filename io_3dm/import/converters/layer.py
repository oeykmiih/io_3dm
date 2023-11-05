# SPDX-License-Identifier: GPL-2.0-or-later
import bpy
import rhino3dm

from io_3dm import utils

RHLAYER_ID = "00000000-0000-0000-0000-000000000000"

def new(rhlay, name=None):
    if name is None:
        name = rhlay.Name
    bllay = utils.bpy.obt(bpy.data.collections, name, force=True)
    return bllay