# SPDX-License-Identifier: GPL-2.0-or-later
import math

import bpy
import rhino3dm
import mathutils

from ... import utils
from . import geometry

def camera(rhcam, options=None, name=None):
    if name is None:
        name = rhcam.Name
    bldata = utils.blpy.obt(bpy.data.cameras, name, force=True, overwrite='SOFT')
    blcam =  utils.blpy.obt(bpy.data.objects, name, data=bldata, force=True, overwrite='SOFT')
    blcam["rhname"] = rhcam.Name

    blcam.location = (rhcam.Viewport.CameraLocation.X, rhcam.Viewport.CameraLocation.Y, rhcam.Viewport.CameraLocation.Z)
    rhdir = geometry.vector(rhcam.Viewport.CameraDirection).to_track_quat('-Z' ,'Y') # Blender camera default rotation is -Z front and Y up.
    blcam.rotation_euler = rhdir.to_euler()

    bldata.lens = rhcam.Viewport.Camera35mmLensLength
    return blcam
