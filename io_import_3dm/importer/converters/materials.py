# SPDX-License-Identifier: GPL-2.0-or-later
import bpy
import bpy_extras
from bpy_extras import node_shader_utils
import rhino3dm

from ... import utils

_BLACK = (0, 0, 0, 255)

class RHINO_DEFAULT:
    Name = "RhinoDefault"
    DiffuseColor = (255, 255, 255, 255)
    Transparency = 0.0

def create_rhino_default(file):
    rhmat = rhino3dm.Material()
    rhmat.Name = RHINO_DEFAULT.Name
    rhmat.DiffuseColor = RHINO_DEFAULT.DiffuseColor
    rhmat.Transparency = RHINO_DEFAULT.Transparency
    file.Materials.Add(rhmat)
    return None

def material(rhmat, name=None, options=None):
    if name is None:
        name = rhmat.Name
    blmat = utils.blpy.obt(bpy.data.materials, name)
    if blmat is None:
        blmat = utils.blpy.obt(bpy.data.materials, name, force=True)
        blmat["rhname"] = rhmat.Name
        blmat["rhid"] = str(rhmat.Id)

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
        blmat.cycles.displacement_method = options.cycles_displacement_method

        principled = bpy_extras.node_shader_utils.PrincipledBSDFWrapper(blmat, is_readonly=False)
        principled.base_color = (r/255.0, g/255.0, b/255.0)
    return blmat
