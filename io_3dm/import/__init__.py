# SPDX-License-Identifier: GPL-2.0-or-later
import functools
import os
import time
import collections

import bpy
import rhino3dm

from io_3dm import utils
addon = utils.bpy.Addon()

MODULES = {
    "properties" : None,
    "converters" : None,
}
MODULES = utils.import_modules(MODULES)

RHINO_INSTANCE_REFERENCE = rhino3dm.ObjectType.InstanceReference

def log(message):
    print(f"{addon.name} :: {message}")
    return None

def profile(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        print(f"{addon.name}" + " >>>>>>> {:.2f} seconds".format(time.time() - start))
        return result
    return wrapper

def timer(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        log("Finished in {:.2f} seconds\n".format(time.time() - start))
        return result
    return wrapper

@timer
def _import(operator, context):
    print()
    options = operator.options
    options.name = operator.name
    update = operator.update

    try:
        rhfile = load_file(path=operator.filepath)
    except Exception as e:
        operator.report({'ERROR'}, f"Failed to load '{operator.filepath}'")
        return {'CANCELLED'}

    patch_options(options)

    pytables = {}
    pytables["collections"] = {}
    pytables["collections"]["project"] = init(context, options=options, update=update)

    options.scale = calculate_scale(context, rhfile)

    if options.filter_cameras and len(rhfile.NamedViews) > 0:
        create_cameras(rhfile.NamedViews, pytables, options=options)

    create_materials(rhfile.Materials, pytables, options=options)

    if len(rhfile.Layers) > 0:
        create_layers(rhfile.Layers, pytables, options=options)

    if update:
        purge()

    if len(rhfile.Objects) > 0:
        handle_objects(rhfile, pytables, options=options)

    link_to_scene(context, pytables["collections"]["project"])
    return {'FINISHED'}

def patch_options(options):
    env_geometry = vars(converters.geometry)

    env_geometry["RHINO_IMPORT"] = env_geometry["RHINO_IMPORT_DEFAULT"].copy()

    if not options.filter_mesh_curves:
        env_geometry["RHINO_IMPORT"].pop(rhino3dm.ObjectType.Curve)

    if options.mesh_faces == 'JOIN':
        env_geometry["rhmesh_join"] = env_geometry["rhmesh_remove_doubles"]

    match options.block_instancing:
        case 'SINGLE_MESH':
            converters.block.definition = converters.block.def_single_mesh
            converters.block.instance = converters.block.ins_single_mesh
    return None

@profile
def init(context, options=None, update=None):
    log("Starting import process")
    if update:
        log("Reload detected")
        blcol = context.scene.collection.children[options.name]
        context.scene.collection.children.unlink(blcol)
        utils.bpy.col.empty(blcol, recursive=True, objects=True)
    else:
        blcol = utils.bpy.col.obt(options.name, force=True, overwrite='NEW')
        options.name = blcol.name
    pr_blcol = getattr(blcol, addon.name)
    pr_blcol["project"] = options.name
    blcol.use_fake_user = True
    return blcol

@profile
def purge():
    log("Purging")
    bpy.data.orphans_purge(do_recursive=True)
    return None

@profile
def link_to_scene(context, blcol):
    log("Linking to scene")
    context.scene.collection.children.link(blcol)
    blcol.use_fake_user = False
    return None

@profile
def post(pytables):
    for blmat in pytables["materials"]:
        blmat.use_fake_user = False
    bpy.data.orphans_purge(do_recursive=True)
    return None

@profile
def load_file(path=None):
    filename = os.path.basename(path)
    log(f"Loading '{filename}'")
    try:
        rhfile = rhino3dm.File3dm.Read(path)
        assert rhfile is not None
    except:
        log(f"Failed to load '{filename}'")
        raise
    return rhfile

@profile
def calculate_scale(context, rhfile):
    log("Calculating unit scale")
    return rhino3dm.UnitSystem.UnitScale(rhfile.Settings.ModelUnitSystem, rhino3dm.UnitSystem.Meters) / context.scene.unit_settings.scale_length

@profile
def create_cameras(rhcams, pytables, options=None):
    log("Importing cameras")
    blcol = pytables["collections"]["cameras"] =  utils.bpy.col.obt(
        f"{options.name}::#Cameras",
        parent=pytables["collections"]["project"],
        force=True,
    )

    for rhcam in rhcams:
        blcam = converters.camera.new(rhcam, f"{options.name}::{rhcam.Name}", options=options)
        blcol.objects.link(blcam)
    return None

@profile
def create_materials(rhmats, pytables, options=None):
    log("Importing materials")
    materials = pytables["materials"] = []
    for rhmat in rhmats:
        blmat = converters.material.new(rhmat, name=rhmat.Name, options=options)
        blmat.use_fake_user = True
        materials.append(blmat)
    blmat = converters.material.default()
    blmat.use_fake_user = True
    materials.append(blmat)
    return None

@profile
def create_layers(rhlayers, pytables, options=None):
    log("Importing layers")
    layers = pytables["layers"] = []
    top_layer = pytables["collections"]["layers"] = utils.bpy.col.obt(
        f"{options.name}::#Layers",
        parent=pytables["collections"]["project"],
        force=True,
    )
    for rhlay in rhlayers:
        bllay = create_layer(rhlay, rhlayers, layers, top_layer, options)
        layers.append(bllay)
    return None

def create_layer(rhlay, rhlayers, layers, top_layer, options=None):
    bllay = converters.layer.new(rhlay, name=f"{options.name}::{rhlay.Name}")

    parent_index = rhlayers.FindId(rhlay.ParentLayerId).Index
    parent_bllay = top_layer if parent_index == -1 else layers[parent_index]

    if bllay.name not in parent_bllay.children:
        parent_bllay.children.link(bllay)
    return bllay

def handle_objects(rhfile, pytables, options=None):
    def _sort(_rhobs):
        rhbks = []
        rhobs = []
        for rhob in _rhobs:
            if rhob.Geometry.ObjectType == RHINO_INSTANCE_REFERENCE:
                rhbks.append(rhob)
            elif not rhob.Attributes.IsInstanceDefinitionObject:
                rhobs.append(rhob)
        return rhobs, rhbks

    layers = pytables["layers"]
    rhobs, rhbks = _sort(rhfile.Objects)

    if options.filter_objects and len(rhobs) > 0:
        create_objects(rhobs, rhfile, pytables, options=options)

    if options.filter_blocks and len(rhbks) > 0:
        create_blocks(rhbks, rhfile, pytables, options=options)
    return None

def get_material(rhob, rhfile, materials, inherited=None):
    match rhob.Attributes.MaterialSource:
        case rhino3dm.ObjectMaterialSource.MaterialFromObject:
            blmat = materials[rhob.Attributes.MaterialIndex]
        case rhino3dm.ObjectMaterialSource.MaterialFromLayer:
            blmat = materials[rhfile.Layers.FindIndex(rhob.Attributes.LayerIndex).RenderMaterialIndex]
        case rhino3dm.ObjectMaterialSource.MaterialFromParent:
            if inherited:
                blmat = inherited["material"]
            else:
                blmat = converters.material.default()
                log("DEBUG :: MaterialFromParent but nothing inherited.")
    return blmat

@profile
def create_objects(rhobs, rhfile, pytables, options=None):
    log("Importing objects")
    materials = pytables["materials"]
    layers = pytables["layers"]

    for rhob in rhobs:
        if rhob.Geometry.ObjectType in converters.geometry.RHINO_IMPORT:
            blob = create_object(rhob, rhfile, materials, options=options)
            layers[rhob.Attributes.LayerIndex].objects.link(blob)
        else:
            pass
    return None

def create_object(rhob, rhfile, materials, options=None, inherited=None):
    rhob_attrs = rhob.Attributes
    rhid = str(rhob_attrs.Id)

    blmat = get_material(rhob, rhfile, materials, inherited=inherited)

    blob = converters.object.new(rhob, options=options)
    blob.data.materials.append(blmat)
    return blob

@profile
def create_blocks(rhobs, rhfile, pytables, options=None):
    log("Importing blocks")
    blocks = pytables["blocks"] = {}
    materials = pytables["materials"]
    layers = pytables["layers"]

    for rhob in rhobs:
        if rhob.Geometry.ObjectType in converters.geometry.RHINO_IMPORT:
            blob = create_block(rhob, rhfile, blocks, materials, options=options)
            layers[rhob.Attributes.LayerIndex].objects.link(blob)
        else:
            pass
    return None

def create_block(rhob, rhfile, blocks, materials, options=None, inherited=None):
    blmat = get_material(rhob, rhfile, materials, inherited=inherited)

    rhdef_rhid = str(rhob.Geometry.ParentIdefId)
    if rhdef_rhid in blocks:
        bldef = blocks[rhdef_rhid]
        blbk = converters.block.instance(rhob, bldef, options=options)
    else:
        rhdef = rhfile.InstanceDefinitions.FindId(rhob.Geometry.ParentIdefId)
        children = []
        inherited = {}
        inherited["material"] = blmat
        for child_rhid in rhdef.GetObjectIds():
            if child_rhid in blocks:
                child_blob = blocks[child_rhid]
            else:
                child_rhob = rhfile.Objects.FindId(child_rhid)
                if child_rhob.Geometry.ObjectType == RHINO_INSTANCE_REFERENCE:
                    child_blob = create_block(child_rhob, rhfile, blocks, materials, options=options, inherited=inherited)
                elif child_rhob.Geometry.ObjectType in converters.geometry.RHINO_IMPORT:
                    child_blob = create_object(child_rhob, rhfile, materials, options=options, inherited=inherited)
                else:
                    continue
                blocks[child_rhid] = child_blob
            children.append(child_blob)
        bldef = blocks[rhdef_rhid] = converters.block.definition(rhdef, children, options=options)
        blbk = converters.block.instance(rhob, bldef, options=options)
    return blbk

class IO3DM_ImportOptions(bpy.types.PropertyGroup):
    name : bpy.props.StringProperty()
    scale : bpy.props.FloatProperty()

    filter_blocks : bpy.props.BoolProperty(
        name = "Blocks",
        default = True,
    )

    filter_cameras : bpy.props.BoolProperty(
        name = "Cameras",
        default = False,
    )

    filter_objects : bpy.props.BoolProperty(
        name = "Objects",
        default = True,
    )

    filter_mesh_curves : bpy.props.BoolProperty(
        name = "Curves",
        default = False,
    )

    mesh_faces : bpy.props.EnumProperty(
        name = "Faces",
        items = [
            ('JOIN',"Join",""),
            ('SPLIT',"Split", ""),
        ],
        default = 'JOIN',
    )

    block_instancing : bpy.props.EnumProperty(
        name = "Instancing",
        items = [
            # ('COLLECTION_INSTANCE',"Collection Instance",""),
            ('SINGLE_MESH',"Single Mesh", ""),
        ],
        default = 'SINGLE_MESH',
    )

    material_displacement : bpy.props.EnumProperty(
        name = "Displacement",
        items = [
            ('BUMP', "Bump Only", ""),
            ('DISPLACEMENT', "Displacement Only", ""),
            ('BOTH', "Both", ""),
        ],
        default = 'BOTH',
    )

class IO3DM_OT_Import(bpy.types.Operator):
    bl_idname = "import_scene.3dm"
    bl_label = "Import 3DM"
    bl_options = {'REGISTER', 'UNDO'}

    def enum_get_loaded(self, context):
        return [(blcol.name, blcol.name, '') for blcol in context.scene.collection.children if "project" in getattr(blcol, addon.name)]

    def get_loaded(self, context):
        return [blcol.name for blcol in context.scene.collection.children if "project" in getattr(blcol, addon.name)]

    def set_name(self, context):
        self.name = self.loaded
        return None

    options : bpy.props.PointerProperty(type = IO3DM_ImportOptions)

    filename_ext = ".3dm"
    filter_glob : bpy.props.StringProperty(
        default = "*.3dm",
        options = {"HIDDEN"},
    )
    filepath : bpy.props.StringProperty(subtype = "FILE_PATH")

    name : bpy.props.StringProperty(
        name = "Name",
        default = "3DM",
    )

    loaded : bpy.props.EnumProperty(
        name = "Loaded",
        items = enum_get_loaded,
        update = set_name,
    )

    update : bpy.props.BoolProperty(
        name = "Overriding",
        default = False,
    )

    def execute(self, context):
        session = addon.session
        session.filepath = self.filepath
        self.update = True if self.name in self.get_loaded(context) else False
        return _import(self, context)

    def draw(self, context):
        layout = self.layout
        options = self.options

        col = layout.box().column()
        col.use_property_split = True
        col.use_property_decorate = False

        loaded = self.get_loaded(context)
        if self.name in loaded:
            utils.bpy.ui.alert(col, text="Overriding")
            col.prop(self, "loaded", text="Reload?")
        else:
            utils.bpy.ui.label(col, text="Creating New", depress=True)
            row = col.row(align=True)
            row.enabled = (len(loaded) > 0)
            row.prop(self, "loaded", text="Reload?")

        col.prop(self, "name")

        col =  layout.box().column()
        col.use_property_split = True
        col.use_property_decorate = False
        col.label(text="Filter")

        col.prop(options, "filter_cameras")
        col.prop(options, "filter_blocks")
        col.prop(options, "filter_objects")

        col =  layout.box().column()
        col.use_property_split = True
        col.use_property_decorate = False
        col.label(text="Blocks")
        col.enabled = options.filter_blocks

        col.prop(options, "block_instancing")

        col =  layout.box().column()
        col.use_property_split = True
        col.use_property_decorate = False
        col.label(text="Mesh")

        col.prop(options, "mesh_faces")

        sub = col.column()
        sub.label(text="Filter")
        sub.prop(options, "filter_mesh_curves")

        col =  layout.box().column()
        col.use_property_split = True
        col.use_property_decorate = False
        col.label(text="Materials")

        col.prop(options, "material_displacement")
        return None

    def invoke(self, context, event):
        session = addon.session
        self.filepath = session.filepath
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

@addon.property
class WindowManager_Import(bpy.types.PropertyGroup):
    filepath : bpy.props.StringProperty(
        subtype = "FILE_PATH"
    )

CLASSES = [
    IO3DM_ImportOptions,
    IO3DM_OT_Import,
    WindowManager_Import,
]

def register():
    utils.bpy.register_modules(MODULES)
    utils.bpy.register_classes(CLASSES)
    return None

def unregister():
    utils.bpy.unregister_classes(CLASSES)
    utils.bpy.unregister_modules(MODULES)
    return None