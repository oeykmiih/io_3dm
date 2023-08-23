# SPDX-License-Identifier: GPL-2.0-or-later
import bpy
import rhino3dm

from ... import utils
from . import geometry

def object(rhob, rhlay, name=None, scale=1, options=None):
    if name is None:
        name = str(rhob.Attributes.Id)
    bldata = geometry.RHINO_IMPORT[rhob.Geometry.ObjectType](rhob, scale, options=options)
    blob =  utils.blpy.obt(bpy.data.objects, name, data=bldata, force=True)
    blob["rhname"] = rhob.Attributes.Name
    blob["rhid"] = str(rhob.Attributes.Id)
    blob["rhlay"] = str(rhlay.Id)
    return blob
