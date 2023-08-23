# SPDX-License-Identifier: GPL-2.0-or-later
import bpy

def enum_from_list(list):
    return [(str(item), str(item), '') for item in list]

def obt(datablock, id, data=None, force=False, overwrite=None):
    """Returns a new object if objects does not exist."""
    if id in datablock:
        match overwrite:
            case 'SOFT':
                datablock[id].name = f"{id}.old"
                bldat = _create(datablock, id, data)
            case 'HARD':
                datablock.remove(datablock[id])
                bldat = _create(datablock, id, data)
            case None:
                bldat = datablock[id]
    elif force:
        bldat = _create(datablock, id, data)
    else:
        bldat = None
    return bldat

def _create(datablock, id, data):
    match datablock:
        case bpy.data.objects | bpy.data.lights:
            bldat = datablock.new(id, data)
        case _:
            bldat = datablock.new(id)
    return bldat
