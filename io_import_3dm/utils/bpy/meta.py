# SPDX-License-Identifier: GPL-2.0-or-later
import builtins
import bpy

from .. import std

def enum_from_list(list, raw=False):
    if raw:
        return [(str(item), str(item).capitalize(), '') for item in list]
    else:
        return [(str(item).upper(), str(item).capitalize(), '') for item in list]

def obt(datablock, id, data=None, scope=None, force=False, overwrite=None):
    """Returns a new object if objects does not exist."""
    if scope is None:
        scope = datablock
    elif len(scope) > 0:
        if type(scope[0]) != builtins.str:
            scope = [item.name for item in scope]
    if id in scope:
        match overwrite:
            case 'NEW':
                bldat = _create(datablock, id, data)
            case 'SOFT':
                datablock[id].name = f"{id}.old"
                bldat = _create(datablock, id, data)
            case 'HARD':
                datablock.remove(datablock[id])
                bldat = _create(datablock, id, data)
            case None:
                bldat = datablock[id]
    elif force:
        if id in datablock:
            datablock[id].name = f"{id}.old"
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

def validate_properties(dictionary):
    return all([std.rgetattr(bpy, attribute) == value for attribute, value in dictionary.items()])
