# SPDX-License-Identifier: GPL-2.0-or-later
import bpy

class UTILS_OT_Placeholder(bpy.types.Operator):
    bl_idname = "utils.placeholder"
    bl_label = ""

    def execute(self, context):
        return {'CANCELLED'}

class UTILS_OT_Select(bpy.types.Operator):
    bl_idname = "utils.select"
    bl_label = "Select Object"
    bl_description = "Shift-Click to toggle selection, Ctrl-Click to remove from selection"
    bl_options = {'UNDO'}

    obj_name: bpy.props.StringProperty()
    toggle: bpy.props.BoolProperty()
    deselect: bpy.props.BoolProperty()
    parent_instead: bpy.props.BoolProperty()

    def invoke(self, context, event):
        self.toggle = event.shift
        self.deselect = event.ctrl
        return self.execute(context)

    def execute(self, context):
        obj = bpy.data.objects.get(self.obj_name)

        if obj is not None:
            if self.parent_instead and obj.parent is not None:
                obj = obj.parent

            if bpy.ops.object.mode_set.poll():
                bpy.ops.object.mode_set(mode="OBJECT")

            if self.toggle:
                if obj.select_get():
                    obj.select_set(False)
                else:
                    obj.select_set(True)
                    bpy.context.view_layer.objects.active = obj
            elif self.deselect:
                obj.select_set(False)
            else:
                bpy.ops.object.select_all(action='DESELECT')
                obj.select_set(True)
                bpy.context.view_layer.objects.active = obj
        return {'FINISHED'}
