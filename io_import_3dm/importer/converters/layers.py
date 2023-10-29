# SPDX-License-Identifier: GPL-2.0-or-later
import bpy
import rhino3dm

from ... import utils

RHINO_TOP_LAYER_ID = "00000000-0000-0000-0000-000000000000"

def layer(rhlay, name=None):
    if name is None:
        name = rhlay.Name
    bllay = utils.blpy.obt(bpy.data.collections, name, force=True)
    bllay["rhname"] = rhlay.Name
    bllay["rhid"] = str(rhlay.Id)
    bllay["rhid_parent"] = str(rhlay.ParentLayerId)
    return bllay
