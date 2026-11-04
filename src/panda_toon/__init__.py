# SPDX-License-Identifier: GPL-3.0-or-later
import bpy
from .material.settings import PandaToonSettings
from .ui.panel import PANDA_TOON_OT_create, PANDA_TOON_PT_material

CLASSES = (PandaToonSettings, PANDA_TOON_OT_create, PANDA_TOON_PT_material)


def register():
    registered = []
    try:
        for cls in CLASSES:
            bpy.utils.register_class(cls)
            registered.append(cls)
        bpy.types.Material.panda_toon = bpy.props.PointerProperty(type=PandaToonSettings)
    except Exception:
        for cls in reversed(registered):
            bpy.utils.unregister_class(cls)
        raise


def unregister():
    if hasattr(bpy.types.Material, "panda_toon"):
        del bpy.types.Material.panda_toon
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
