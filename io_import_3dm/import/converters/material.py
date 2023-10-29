# SPDX-License-Identifier: GPL-2.0-or-later
import bpy
import bpy_extras
from bpy_extras import node_shader_utils
import rhino3dm

from io_import_3dm import utils

_BLACK = (0, 0, 0, 255)

class RHINO_DEFAULT:
    Name = "RhinoDefault"
    DiffuseColor = (255, 255, 255, 255)

def default(options=None):
    blmat = utils.bpy.obt(bpy.data.materials, RHINO_DEFAULT.Name)
    if blmat is None:
        blmat = utils.bpy.obt(bpy.data.materials, RHINO_DEFAULT.Name, force=True)

        blmat.use_nodes = True
        principled = bpy_extras.node_shader_utils.PrincipledBSDFWrapper(blmat, is_readonly=False)
        principled.base_color = (
            RHINO_DEFAULT.DiffuseColor[0]/255.0,
            RHINO_DEFAULT.DiffuseColor[1]/255.0,
            RHINO_DEFAULT.DiffuseColor[2]/255.0
        )
    return blmat

def new(rhmat, name=None, options=None):
    blmat = utils.bpy.obt(bpy.data.materials, name)
    if blmat is None:
        blmat = utils.bpy.obt(bpy.data.materials, name, force=True)

        if rhmat.DiffuseColor == _BLACK and rhmat.Reflectivity > 0.0 and rhmat.Transparency == 0.0:
            r, g, b, _ = rhmat.ReflectionColor
        elif rhmat.DiffuseColor == _BLACK and rhmat.Reflectivity == 0.0 and rhmat.Transparency > 0.0:
            r, g, b, _ = rhmat.TransparentColor
        elif rhmat.DiffuseColor == _BLACK and rhmat.Reflectivity > 0.0 and rhmat.Transparency > 0.0:
            r, g, b, _ = rhmat.TransparentColor
        else:
            r, g, b, _ = rhmat.DiffuseColor

        blmat.use_nodes = True
        blmat.diffuse_color[3] = 1.0-rhmat.Transparency # Viewport transparency
        # blmat.cycles.displacement_method = options.cycles_displacement_method

        principled = bpy_extras.node_shader_utils.PrincipledBSDFWrapper(blmat, is_readonly=False)
        principled.base_color = (r/255.0, g/255.0, b/255.0)
    return blmat
