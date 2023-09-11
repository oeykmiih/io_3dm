# SPDX-License-Identifier: GPL-2.0-or-later
import os
import time
import collections

import bpy
import bmesh
import mathutils
import rhino3dm

from .. import addon
from .. import utils

from . import converters

class IO3DM_PROPS_Project(bpy.types.PropertyGroup):
    layers: bpy.props.StringProperty()

class IO3DM_Importer:
    def __init__(self, operator, context):
        self.operator = operator
        self.context = context
        self.options = operator.options
        self.reload = operator.reload
        self.name = operator.project_existing if operator.reload else operator.project_new
        self.file = None
        self.time = 0
        self.time_start = 0

        self.project = None
        self.unit_scale = None
        self.containers = {}
        self.materials = {}
        self.layers = {}
        self.block_def = {}
        self.block_obs = {}
        self.block_pairs = {}

    def log(self, message):
        print(f"{addon.name} :: {message}")
        return None

    def verb(self, message):
        if self.operator.log_level == 'VERBOSE':
            self.log(f"{message}")
        return None

    def debug(self, message):
        if self.operator.log_level == 'VERBOSE' and True:
            print(f"{addon.name} >> {message}")
        return None

    def profile_code(self, end):
        if end and self.operator.log_level == 'VERBOSE':
            print(f"{addon.name}" + " >>>>>>> {:.2f} seconds".format(time.time() - self.time))
        self.time = time.time()
        return None

    def timer(self):
        if not self.time_start:
            self.time_start = time.time()
        else:
            self.log("Import finished in {:.2f} seconds".format(time.time() - self.time_start))
        return None

    def execute(self):
        print("\n")
        self.timer()
        self.check_loaded(self.context)
        self.cleanup_pre()
        if self.load_file():
            return None
        self.calculate_unit_scale()
        self.create_cameras()
        self.create_materials()
        self.create_layers()
        self.create_block_def()
        self.create_objects()
        self.populate_instances()
        self.import_to_scene(self.context)
        # self.cleanup_post()
        self.timer()
        return None

    def check_loaded(self, context):
        self.profile_code(False)
        self.log("Starting import process")
        if self.reload:
            self.project = context.scene.collection.children[self.name]
            context.scene.collection.children.unlink(self.project)
        else:
            self.project = utils.blcol.obt(self.name, force=True, overwrite='HARD')
            self.project["io3dm"] = {}
        self.project.use_fake_user = True
        self.profile_code(True)
        return None

    def cleanup_pre(self):
        if not self.reload:
            return None
        self.profile_code(False)
        self.log("Reload detected. Purging first")
        utils.blcol.unlink(self.project, recursive=True, objects=True)
        self.profile_code(True)
        return None

    def load_file(self):
        self.profile_code(False)
        file_name = os.path.basename(self.operator.filepath.split(".")[0])
        self.log(f"Loading \"{file_name}\"")
        try:
            self.file = rhino3dm.File3dm.Read(self.operator.filepath)
        except:
            self.log(f"Failed to load '{file_name}' \n")
        self.profile_code(True)
        return None

    def calculate_unit_scale(self):
        self.unit_scale = rhino3dm.UnitSystem.UnitScale(self.file.Settings.ModelUnitSystem, rhino3dm.UnitSystem.Meters) / bpy.context.scene.unit_settings.scale_length
        self.log(f"File scale is: {self.unit_scale}")
        return None

    def create_cameras(self):
        if not self.options.filter_cameras:
            return None
        if len(self.file.NamedViews) == 0:
            return None
        self.profile_code(False)
        self.log("Importing cameras")
        self.containers["cameras"] = utils.blcol.obt(f"{self.name}#Cameras", parent=self.project, force=True)
        for rhcam in self.file.NamedViews:
            blcam = converters.camera(rhcam, name=f"{self.name}:{rhcam.Name}", options=self.options)
            if blcam.name not in self.containers["cameras"].objects:
                self.containers["cameras"].objects.link(blcam)
        self.profile_code(True)
        return None

    def create_materials(self):
        if not self.options.filter_materials:
            return None
        self.profile_code(False)
        self.log("Importing materials")
        converters.materials.create_rhino_default(self.file)
        for rhmat in self.file.Materials:
            blmat = self.materials[rhmat.Name] = converters.material(rhmat, options=self.options)
            blmat.use_fake_user = True
        self.profile_code(True)
        return None

    def create_layers(self):
        self.profile_code(False)
        self.log("Importing layers")
        self.containers["layers"] = utils.blcol.obt(f"{self.name}#Layers", parent=self.project, force=True)
        self.layers[converters.RHINO_TOP_LAYER_ID] = self.containers["layers"]
        self.verb(":: creating layers")
        for rhlay in self.file.Layers:
            if not rhlay.Visible:
                # self.verb(f":: :: \"{rhlay}\" layer is hidden, skipped")
                continue
            self.create_layer(rhlay)
        self.profile_code(True)
        self.verb(":: cleaning remnants")
        bpy.data.orphans_purge(do_recursive=True)
        self.profile_code(True)
        return None

    def create_layer(self, rhlay):
        if str(rhlay.Id) not in self.layers:
            bllay = self.layers[str(rhlay.Id)] = converters.layer(rhlay, name=f"{self.name}:{rhlay.Name}")
            if str(rhlay.ParentLayerId) not in self.layers:
                self.create_layer(self.file.Layers.FindId(rhlay.ParentLayerId))
            if bllay.name not in self.layers[str(rhlay.ParentLayerId)].children:
                self.layers[str(rhlay.ParentLayerId)].children.link(bllay)
        return None

    def create_block_def(self):
        if len(self.file.InstanceDefinitions) == 0:
            return None
        self.profile_code(False)
        self.log("Importing blocks")
        match self.options.block_instancing:
            case 'COLLECTION_INSTANCE':
                self.containers["blocks"] = utils.blcol.obt(f"{self.name}#Blocks", force=True)
                for rhdef in self.file.InstanceDefinitions:
                    bldef = self.block_def[str(rhdef.Id)] = converters.blocks.def_collection_instance(rhdef, name=f"{self.name}:{rhdef.Name}")
                    for rhid in rhdef.GetObjectIds():
                        self.block_obs[str(rhid)] = bldef
                    if bldef.name not in self.containers["blocks"].children:
                        self.containers["blocks"].children.link(bldef)
            case 'SINGLE_MESH':
                for rhdef in self.file.InstanceDefinitions:
                    bldef = self.block_def[str(rhdef.Id)] = converters.blocks.def_single_mesh(rhdef, name=f"{self.name}:{rhdef.Name}")
                    self.block_pairs[str(rhdef.Id)] = collections.deque()
                    for rhid in rhdef.GetObjectIds():
                        self.block_obs[str(rhid)] = str(rhdef.Id)
        self.profile_code(True)
        return None

    def create_objects(self):
        if not self.options.filter_objects:
            return None
        if len(self.file.Objects) == 0:
            return None
        self.profile_code(False)
        self.log("Importing objects")
        for rhob in self.file.Objects:
            if rhob.Geometry.ObjectType not in converters.RHINO_IMPORT:
                # self.debug(f":: :: \"{rhid}\" skipped.")
                # self.debug(f":: :: {rhob.Geometry.ObjectType} not supported yet.")
                continue
            rhid = str(rhob.Attributes.Id)
            if not rhob.Attributes.Visible:
                # self.verb(f":: :: {rhid} object is hidden, skipped")
                continue
            rhlay = self.file.Layers.FindIndex(rhob.Attributes.LayerIndex)
            if not rhlay.Visible:
                # self.verb(f":: :: {rhid} layer is hidden, skipped")
                continue
            match self.options.block_instancing:
                case 'COLLECTION_INSTANCE':
                    if rhob.Geometry.ObjectType == rhino3dm.ObjectType.InstanceReference:
                        blob = converters.blocks.ref_collection_instance(rhob, name=f"{self.name}:{rhid}", scale=self.unit_scale)
                        blob.instance_collection = self.block_def[str(rhob.Geometry.ParentIdefId)]
                    else:
                        blob = self.create_object(rhob, rhid, rhlay)

                    if rhid in self.block_obs.keys():
                        self.block_obs[rhid].objects.link(blob)
                    else:
                        self.layers[str(rhlay.Id)].objects.link(blob)
                case 'SINGLE_MESH':
                    if rhob.Geometry.ObjectType == rhino3dm.ObjectType.InstanceReference:
                        bldef = self.block_def[str(rhob.Geometry.ParentIdefId)]
                        blob = converters.blocks.ref_single_mesh(rhob, bldef, name=f"{self.name}:{rhid}", scale=self.unit_scale)
                    else:
                        blob = self.create_object(rhob, rhid, rhlay)

                    if rhid in self.block_obs.keys():
                        if rhob.Geometry.ObjectType == rhino3dm.ObjectType.InstanceReference:
                            self.block_pairs[self.block_obs[rhid]].append(blob)
                        else:
                            self.block_pairs[self.block_obs[rhid]].appendleft(blob)
                    else:
                        self.layers[str(rhlay.Id)].objects.link(blob)
        self.profile_code(True)
        return None

    def create_object(self, rhob, rhid, rhlay):
        blob = converters.object(rhob, rhlay, name=f"{self.name}:{rhid}", scale=self.unit_scale, options=self.options)
        match rhob.Attributes.MaterialSource:
            case rhino3dm.ObjectMaterialSource.MaterialFromLayer:
                rhmat = self.file.Materials.FindIndex(rhlay.RenderMaterialIndex)
            case rhino3dm.ObjectMaterialSource.MaterialFromObject:
                rhmat = self.file.Materials.FindIndex(rhob.Attributes.MaterialIndex)
        if rhmat.Name == '':
            blmat = self.materials[converters.materials.RHINO_DEFAULT.Name]
        else:
            blmat = self.materials[rhmat.Name]
        blob.data.materials.append(blmat)
        return blob

    def populate_instances(self):
        if len(self.file.InstanceDefinitions) == 0:
            return None
        match self.options.block_instancing:
            case 'COLLECTION_INSTANCE':
                return None
            case 'SINGLE_MESH':
                self.profile_code(False)
                self.log("Populating instances")
                for rhdef_id in self.block_pairs.keys():
                    bldef = self.block_def[rhdef_id]
                    converters.blocks.pop_single_mesh(bldef, self.block_pairs[rhdef_id], self.options)
                self.profile_code(True)
        return None

    def import_to_scene(self, context):
        self.log("Linking to scene")
        self.profile_code(False)
        context.scene.collection.children.link(self.project)
        self.project.use_fake_user = False
        for blmat in self.materials.values():
            blmat.use_fake_user = False
        self.profile_code(True)
        return None

    def cleanup_post(self):
        self.log("Cleaning remnants")
        self.profile_code(False)
        bpy.data.orphans_purge(do_recursive=True)
        self.profile_code(True)
        return None
