# SPDX-License-Identifier: GPL-2.0-or-later
import mathutils

import bpy
import rhino3dm

from io_3dm import utils

def def_single_mesh(rhdef, children, name=None, options=None):
    name = name if name is not None else rhdef.Name

    bldata = utils.bpy.obt(bpy.data.meshes, str(rhdef.Id), force=True)
    bldef =  utils.bpy.obt(bpy.data.objects, name, data=bldata, force=True)
    utils.bpy.obj.join(bldef, children)

    return bldef

def ins_single_mesh(rhref, bldef, name=None, options=None):
    name = name if name is not None else str(rhref.Attributes.Id)

    blref =  utils.bpy.obt(bpy.data.objects, name, data=bldef.data, force=True)

    transform=list(rhref.Geometry.Xform.ToFloatArray(1))
    transform=[transform[0:4],transform[4:8], transform[8:12], transform[12:16]]
    transform[0][3] *= 1
    transform[1][3] *= 1
    transform[2][3] *= 1

    blref.matrix_world = mathutils.Matrix(transform)

    return blref

def def_collection_instance(rhdef, name=None):
    name = name if name is not None else rhdef.Name
    bldef = utils.bpy.obt(bpy.data.collections, name, force=True)
    return bldef

def ref_collection_instance(rhref, name=None, scale=1.0):
    iname = name if name is not None else str(rhref.Attributes.Id)
    blref = utils.bpy.obt(bpy.data.objects, name, force=True)

    blref.empty_display_size=0.5
    blref.empty_display_type='PLAIN_AXES'
    blref.instance_type='COLLECTION'

    transform=list(rhref.Geometry.Xform.ToFloatArray(1))
    transform=[transform[0:4],transform[4:8], transform[8:12], transform[12:16]]
    transform[0][3]*=scale
    transform[1][3]*=scale
    transform[2][3]*=scale

    blref.matrix_world = mathutils.Matrix(transform)
    return blref