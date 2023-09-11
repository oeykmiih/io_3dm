# SPDX-License-Identifier: GPL-2.0-or-later
import logging

import bpy
import bpy_extras.io_utils

from .. import addon
from .. import utils

from . import importer

class IO3DM_ImportOptions(bpy.types.PropertyGroup):
    cycles_displacement_method : bpy.props.EnumProperty(
        name = "Material Displacement Method",
        items = [
            ('BUMP', "Bump Only", ""),
            ('DISPLACEMENT', "Displacement Only", ""),
            ('BOTH', "Both", ""),
        ],
        default = 'BUMP',
    )

    filter_blocks : bpy.props.BoolProperty(
        name = "Blocks",
        default = True,
    )

    filter_cameras : bpy.props.BoolProperty(
        name = "Cameras",
        default = False,
    )

    filter_materials : bpy.props.BoolProperty(
        name = "Materials",
        default = True,
    )

    filter_objects : bpy.props.BoolProperty(
        name = "Objects",
        default = True,
    )

    mesh_faces : bpy.props.EnumProperty(
        name = "Faces",
        items = [
            ('SPLIT','Split', ''),
            ('JOIN','Join',''),
        ],
        default = 'JOIN',
    )

    mesh_shading : bpy.props.EnumProperty(
        name = "Faces",
        items = [
            ('FLAT','Flat',''),
            ('SMOOTH','Smooth', ''),
        ],
        default = 'SMOOTH',
    )

    block_instancing : bpy.props.EnumProperty(
        name = "Block Instancing",
        items = [
            ('COLLECTION_INSTANCE','Collection Instance',''),
            ('SINGLE_MESH','Single Mesh', ''),
        ],
        default = 'SINGLE_MESH',
    )
    pass

class IO3DM_OT_Load(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    bl_idname = f"{addon.name}.load"
    bl_label = "Import Rhino3D (.3dm)"
    bl_options = {"REGISTER", "UNDO"}

    def get_projects_enum(self, context):
        return [(blcol.name, blcol.name, '') for blcol in context.scene.collection.children if "io3dm" in blcol]

    def get_projects_names(self, context):
        return [blcol.name for blcol in context.scene.collection.children if "io3dm" in blcol]

    filename_ext = ".3dm"

    filepath: bpy.props.StringProperty(
        subtype = "FILE_PATH"
    )

    filter_glob: bpy.props.StringProperty(
        default = "*.3dm",
        options = {"HIDDEN"},
    )

    log_level : bpy.props.EnumProperty(
        name = "Log Level",
        description = "Import Blocks as:",
        items = [
            ('USER', "User", ""),
            ('VERBOSE',"Verbose", ""),
        ],
        default = 'VERBOSE',
    )

    options : bpy.props.PointerProperty(
        type = IO3DM_ImportOptions,
    )

    project_existing : bpy.props.EnumProperty(
        name = "Projects to Reload",
        items = get_projects_enum,
        default = None,
    )

    project_new: bpy.props.StringProperty(
        name = "New Project",
        default = "3DM",
    )

    reload : bpy.props.BoolProperty(
        name = "Reload?",
        default = False,
    )

    def execute(self, context):
        if self.project_new in self.get_projects_names(context):
            self.reload = True
        import_3dm = importer.IO3DM_Importer(self, context)
        try:
            import_3dm.execute()
        except Exception as e:
            self.report({"ERROR"}, "import_3dm :: An error has occurred, check logs in system console.")
            import_3dm.log("An error has occurred. Exiting early.")
            logging.exception("An error has occurred. Exiting early.")
            return {"CANCELLED"}
        return {"FINISHED"}

    def draw(self, context):
        session = addon.session()
        layout = self.layout
        layout = layout.box()

        col = layout.column()
        row = col.row(align=True)
        row.prop(
            self,
            "reload",
            text = "Already used. Will reload." if not self.reload and self.project_new in self.get_projects_names(context) else None,
            toggle = True)
        if not self.reload:
            col.prop(self, "project_new", text="")
        else:
            col.prop(self, "project_existing", text="")

        col = layout.column(align=True)
        col.prop(self.options, "filter_objects", toggle=True)
        sub = col.column(align=True)
        sub.enabled = self.options.filter_objects
        sub.row(align=True).prop(self.options, "mesh_faces", expand=True)
        sub.row(align=True).prop(self.options, "mesh_shading", expand=True)

        col = layout.column(align=True)
        col.enabled = self.options.filter_objects
        col.operator(utils.UTILS_OT_Placeholder.bl_idname, text="Blocks", depress=False)
        col.row(align=True).prop(self.options, "block_instancing", expand=True)

        col = layout.column(align=True)
        col.prop(self.options, "filter_materials", toggle=True)

        col = layout.column(align=True)
        col.prop(self.options, "filter_cameras", toggle=True)

        row = layout.row()
        row.prop(self, "log_level", expand=True)
        return None

def IO3DM_BT_Import(self, context):
    self.layout.operator(IO3DM_OT_Load.bl_idname, text="Rhino3D (.3dm)")
    return None
