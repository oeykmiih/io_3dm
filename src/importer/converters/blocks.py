# SPDX-License-Identifier: GPL-2.0-or-later
import mathutils

import bpy
import rhino3dm

from ... import utils

def def_collection_instance(rhdef, name=None):
    if name is None:
        name = rhdef.Name
    bldef = utils.blpy.obt(bpy.data.collections, name, force=True)
    bldef["rhname"] = rhdef.Name
    bldef["rhid"] = str(rhdef.Id)
    return bldef

def ref_collection_instance(rhref, name=None, scale=1.0):
    if name is None:
        str(rhref.Attributes.Id)
    blref = utils.blpy.obt(bpy.data.objects, name, force=True)
    blref["rhname"] = rhref.Attributes.Name
    blref["rhid"] = str(rhref.Attributes.Id)

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

def def_single_mesh(rhdef, name=None):
    if name is None:
        name = rhdef.Name
    bldata = utils.blpy.obt(bpy.data.meshes, str(rhdef.Id), force=True)
    bldef =  utils.blpy.obt(bpy.data.objects, name, data=bldata, force=True)
    bldef["rhname"] = rhdef.Name
    bldef["rhid"] = str(rhdef.Id)
    return bldef

def ref_single_mesh(rhref, bldef, name=None, scale=1.0):
    if name is None:
        name = str(rhref.Attributes.Id)
    blref =  utils.blpy.obt(bpy.data.objects, name, data=bldef.data, force=True)
    blref["rhname"] = rhref.Attributes.Name
    blref["rhid"] = str(rhref.Attributes.Id)

    transform=list(rhref.Geometry.Xform.ToFloatArray(1))
    transform=[transform[0:4],transform[4:8], transform[8:12], transform[12:16]]
    transform[0][3]*=scale
    transform[1][3]*=scale
    transform[2][3]*=scale

    blref.matrix_world = mathutils.Matrix(transform)
    return blref

def pop_single_mesh(bldef, bldef_obs):
    utils.blob.join(bldef, bldef_obs)
    return None
