# SPDX-License-Identifier: GPL-2.0-or-later
import math

import bpy
import rhino3dm
import mathutils

from io_3dm import utils

from . import geometry

def new(rhcam, name=None, options=None):
    if name is None:
        name = rhcam.Name
    bldata = utils.bpy.obt(bpy.data.cameras, name, force=True, overwrite='NEW')
    blcam =  utils.bpy.obt(bpy.data.objects, name, data=bldata, force=True, overwrite='NEW')

    blcam.location = (rhcam.Viewport.CameraLocation.X, rhcam.Viewport.CameraLocation.Y, rhcam.Viewport.CameraLocation.Z)

    # Blender camera default rotation is -Z front and Y up.
    rhdir = geometry.vector(rhcam.Viewport.CameraDirection).to_track_quat('-Z' ,'Y')
    blcam.rotation_euler = rhdir.to_euler()

    bldata.lens = rhcam.Viewport.Camera35mmLensLength
    return blcam