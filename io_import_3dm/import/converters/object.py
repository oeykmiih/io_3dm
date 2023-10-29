# SPDX-License-Identifier: GPL-2.0-or-later
import bpy
import rhino3dm

from io_import_3dm import utils
from . import geometry

def new(rhob, name=None, options=None):
    if name is None:
        name = str(rhob.Attributes.Id)
    bldata = geometry.RHINO_IMPORT[rhob.Geometry.ObjectType](rhob, options.scale, options=options)
    blob =  utils.bpy.obt(bpy.data.objects, name, data=bldata, force=True)
    return blob