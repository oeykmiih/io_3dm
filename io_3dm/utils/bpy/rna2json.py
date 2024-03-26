# SPDX-License-Identifier: GPL-2.0-or-later
import json
import os

import bpy

from .. import std

ignore_default = False

typemap = {}
REF_CLASSES = set()
EXC_CLASSES = (
    bpy.types.Operator,
    bpy.types.Menu,
    bpy.types.Panel,
    bpy.types.KeyingSet,
    bpy.types.Header,
)
INC_TYPEMAP = {}
EXC_TYPEMAP = {
    bpy.types.ID : [
        'animation_data',
        'asset_data',
        'bl_description',
        'bl_icon',
        'bl_label',
        'grease_pencil',
        'is_runtime_data',
        'library_weak_reference',
        'library',
        'override_library',
        'preview',
        'tag',
        'use_extra_user',
        'use_fake_user',
    ]
}

def _build_property_typemap(inc_typemap, exc_typemap):
    global typemap
    typemap_str = {}

    inc_typemap_keys = inc_typemap.keys()
    exc_typemap_keys = exc_typemap.keys()

    for attr in dir(bpy.types):
        if attr.startswith("_"):
            continue

        cls = getattr(bpy.types, attr)
        if issubclass(cls, EXC_CLASSES):
            continue

        bl_rna = getattr(cls, "bl_rna", None)
        # Needed to skip classes added to the modules `__dict__`.
        if bl_rna is None:
            continue

        attr_type = type(bl_rna)

        properties = []

        inc_props = []
        exc_props = []

        if attr_type in inc_typemap_keys:
            inc_props.extend(inc_typemap[attr_type])

        if attr_type in exc_typemap_keys:
            exc_props.extend(exc_typemap[attr_type])

        for t in type(bl_rna).__mro__:
            if t in inc_typemap_keys:
                inc_props.extend(inc_typemap[t])
            if t in exc_typemap_keys:
                exc_props.extend(exc_typemap[t])

        if len(inc_props) > 0:
            rna_keys = bl_rna.properties.keys()
            for prop_id in inc_props:
                if prop_id in rna_keys:
                    prop = bl_rna.properties[prop_id]
                    if not prop.is_skip_save:
                        if not prop.is_readonly or type(prop) in (bpy.types.PointerProperty, bpy.types.CollectionProperty):
                            properties.append(prop_id)
        elif len(exc_props) > 0:
            for prop_id, prop in bl_rna.properties.items():
                if prop_id not in exc_props:
                    if not prop.is_skip_save:
                        if not prop.is_readonly or type(prop) in (bpy.types.PointerProperty, bpy.types.CollectionProperty):
                            properties.append(prop_id)
        else:
            for prop_id, prop in bl_rna.properties.items():
                if not prop.is_skip_save:
                    if not prop.is_readonly:
                        properties.append(prop_id)
                    else:
                        if type(prop) in (bpy.types.PointerProperty, bpy.types.CollectionProperty):
                            properties.append(prop_id)
                        elif attr_type == bpy.types.NodeTreeInterfaceSocket and prop_id == "in_out":
                            properties.append(prop_id)

        if "rna_type" in properties:
            properties.remove("rna_type")
        typemap[attr_type] = properties
        typemap_str[attr] = properties

    with open(os.path.join(os.getcwd(), "ark\\_tests\\rna_cliboard_TYPEMAP.json"), 'w') as file:
        file.write(json.dumps(typemap_str))
    return None

def _build_property_group_map(attr):
    bl_rna = getattr(attr, "bl_rna", None)
    # Needed to skip classes added to the modules `__dict__`.
    if bl_rna is None:
        return None

    # # to support skip-save we can't get all props
    properties = bl_rna.properties.keys()
    properties = []
    for prop_id, prop in bl_rna.properties.items():
        if not prop.is_skip_save:
            if not prop.is_readonly or type(prop) in (bpy.types.PointerProperty, bpy.types.CollectionProperty):
                    properties.append(prop_id)

    if "rna_type" in properties:
        properties.remove("rna_type")
    return properties

def _rna2json_node(node, data, parent, exc_props=[]):
    def items2node(prop, subdata, subdata_fixed, data, exc_props=[]):
        if issubclass(subdata_fixed, EXC_CLASSES) or subdata == parent:
            pass
        else:
            subdata_node = node[prop] = {}
            _rna2json_node(subdata_node, subdata, data, exc_props=exc_props)
    data_type = type(data)

    if issubclass(data_type, EXC_CLASSES):
        return None

    # NOTE: point-cache has eternal nested pointer to itself.
    if data == parent:
        return None

    if data_type not in typemap:
        try:
            typemap[data_type] = _build_property_group_map(data)
        except Exception:
            import traceback
            print(traceback.format_exc())
            print(data_type, data, parent, node)
            return node

    for prop in typemap[data_type]:
        if prop in exc_props:
            continue

        subdata = getattr(data, prop)
        if subdata == data:
            continue

        prop_rna = data.bl_rna.properties[prop]
        if ignore_default and subdata == getattr(prop_rna, "default", None):
            continue

        prop_exc = []

        prop_type = type(prop_rna.rna_type)
        match prop_type:
            case bpy.types.BoolProperty:
                node[prop] = subdata
            case bpy.types.StringProperty | bpy.types.EnumProperty:
                node[prop] = subdata
            case bpy.types.FloatProperty | bpy.types.IntProperty:
                if prop_rna.is_array:
                    node[prop] = []
                    for i in range(prop_rna.array_length):
                        node[prop].append(subdata[i])
                else:
                    node[prop] = subdata
            case bpy.types.CollectionProperty:
                subdata_node = node[prop] = []

                for subdata_item in subdata:
                    if subdata_item is not None:
                        item_node = _rna2json_node({}, subdata_item, data)
                        subdata_node.append(item_node)

            case bpy.types.PointerProperty:
                subdata_fixed = type(prop_rna.fixed_type)
                items2node(prop, subdata, subdata_fixed, data)
    return node

def _rna2json_path(rna_path):
    tokens = rna_path.split(".")
    head = tokens.pop(0)
    if head == "bpy":
        root = {}
        id = tokens.pop(0)
        root[id] = {}
        node = root[id]

        for token in tokens:
            node[token] = {}
            node = node[token]

        relative_path = ".".join(tokens)
        attr = getattr(bpy, id).path_resolve(relative_path)

        _rna2json_node(node, attr, None)
        return root
    else:
        raise Exception("Invalid RNA path: %s" % rna_path)

def dump(rna_path: str) -> str:
    _build_property_typemap(INC_TYPEMAP, EXC_TYPEMAP)
    root = _rna2json_path(rna_path)
    return json.dumps(root)

def dump_to_file(rna_path: str, file_path: str) -> None:
    json_str = dump(rna_path)

    with open(file_path, 'w') as file:
        file.write(json_str)
    return None

def dump_multiple(rna_paths: list) -> None:
    _build_property_typemap(INC_TYPEMAP, EXC_TYPEMAP)

    root = {}
    for rna_path in rna_paths:
        root = dict(std.mergedicts(root, _rna2json_path(rna_path)))

    return json.dumps(root)

def dump_multiple_to_file(rna_paths: list, file_path: str) -> None:
    json_str = dump_multiple(rna_paths)

    with open(file_path, 'w') as file:
        file.write(json_str)
    return None

def _json2rna_node(node, data, exc_props={"bl_idname"}) -> None:
    rna_props = data.bl_rna.properties
    rna_keys = rna_props.keys()

    for prop in node:
        if prop not in rna_keys:
            continue

        prop_rna = rna_props[prop]

        match type(prop_rna.rna_type):
            case bpy.types.BoolProperty:
                if not prop_rna.is_readonly:
                    setattr(data, prop, node[prop])
            case bpy.types.StringProperty | bpy.types.EnumProperty:
                if not prop_rna.is_readonly:
                    setattr(data, prop, node[prop])
            case bpy.types.FloatProperty | bpy.types.IntProperty:
                if not prop_rna.is_readonly:
                    setattr(data, prop, node[prop])
            case bpy.types.CollectionProperty:
                subdata = getattr(data, prop)
                subnode = node[prop]

                fixed_type = type(prop_rna.fixed_type)

                if len(subdata) < len(subnode):
                    raise NotImplementedError("This type has not been implemented: %s. %s in %s" %(fixed_type, prop, data))

                if len(subdata) == len(subnode):
                    for i, subnode_item in enumerate(subnode):
                        _json2rna_node(subnode_item, subdata[i])
                elif len(subdata) > len(subnode):
                    for i, subnode_item in enumerate(subnode):
                        _json2rna_node(subnode_item, subdata[i])

                    for i in range(len(subnode), len(subdata)):
                        subdata.remove(subdata[i])

                subdata.update()
            case bpy.types.PointerProperty:
                subdata = getattr(data, prop)
                fixed_type = type(prop_rna.fixed_type)

                _json2rna_node(node[prop], subdata)

                if fixed_type in {bpy.types.CurveMapping}:
                    subdata.update()
    return None

def _json2rna_root(root: str) -> None:
    for key in root.keys():
        attr = getattr(bpy, key)
        node = root[key]

        _json2rna_node(node, attr)
    return None

def load(json_str: str) -> None:
    root = json.loads(json_str)
    _json2rna_root(root)
    return None

def load_from_file(file_path: str) -> None:
    with open(file_path, 'r') as file:
        json_str = file.read()

    load(json_str)
    return None