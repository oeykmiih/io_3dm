# SPDX-License-Identifier: GPL-2.0-or-later
import bpy

name = __package__.split(".", 1)[0]

def preferences():
    """bpy.context.preferences.addons[demo].preferences"""
    return bpy.context.preferences.addons[name].preferences

def session():
    """bpy.context.window_manager.demo"""
    return getattr(bpy.context.window_manager, name)

def props(location):
    return eval(f"getattr(bpy.context.{location}, name)")

def set_props(cls):
    location = cls.__name__.split("_")[-1]
    exec(f"setattr(bpy.types.{location}, name, bpy.props.PointerProperty(type=cls))")
    return None

def del_props(cls):
    location = cls.__name__.split("_")[-1]
    exec(f"delattr(bpy.types.{location}, name)")
    return None
