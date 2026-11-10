# SPDX-License-Identifier: GPL-3.0-or-later
import bpy
from ..material.service import create_material
from ..nodes.core import SCHEMA, VERSION, inspect


class PANDA_TOON_OT_create(bpy.types.Operator):
    bl_idname = "panda_toon.create_material"
    bl_label = "New Panda Toon Material"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.object
        return bool(obj and obj.type == "MESH" and obj.mode == "OBJECT"
                    and obj.data.is_editable and obj.is_editable)

    def execute(self, context):
        obj = context.object
        if obj.data.users > 1:
            self.report({"ERROR"}, "Make mesh data single-user before adding a material")
            return {"CANCELLED"}
        material = create_material()
        # Append; never replace existing slots or polygon assignments.
        obj.data.materials.append(material)
        obj.active_material_index = len(obj.data.materials) - 1
        self.report({"INFO"}, "Material added; assign faces manually if slots already existed")
        return {"FINISHED"}


class PANDA_TOON_PT_material(bpy.types.Panel):
    bl_label = "Panda Toon Material"
    bl_idname = "PANDA_TOON_PT_material"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"

    def draw(self, context):
        layout = self.layout
        layout.operator("panda_toon.create_material", icon="MATERIAL")
        if context.scene.render.engine != "BLENDER_EEVEE":
            layout.label(text="Use EEVEE for Panda Toon", icon="INFO")
        mat = context.material
        if not mat or SCHEMA not in mat:
            return
        try:
            inspect(mat)
        except ValueError as exc:
            layout.label(text=str(exc), icon="ERROR")
            return
        col = layout.column()
        col.enabled = mat.is_editable
        for name in ("base_color", "texture", "threshold_low", "threshold_high"):
            col.prop(mat.panda_toon, name)
        if mat[SCHEMA] == VERSION:
            col.prop(mat.panda_toon, "shadow_edge_softness", slider=True)
        for name in ("light_tone", "mid_tone", "dark_tone"):
            col.prop(mat.panda_toon, name)
        if mat.panda_toon.last_error:
            layout.label(text=mat.panda_toon.last_error, icon="ERROR")
