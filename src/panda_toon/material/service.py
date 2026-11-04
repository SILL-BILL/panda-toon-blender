# SPDX-License-Identifier: GPL-3.0-or-later
import bpy
from ..nodes.core import build_new

_initializing = {}


def _claim_new_material(material):
    """One-shot permission, valid only during our allocation call."""
    key = material.as_pointer()
    if _initializing.get(key) is not material:
        raise ValueError("Initialization is restricted to newly allocated Panda Toon materials")
    del _initializing[key]


def create_material(name="Panda Toon"):
    material = bpy.data.materials.new(name)
    key = material.as_pointer()
    _initializing[key] = material
    try:
        build_new(material)
    except Exception:
        bpy.data.materials.remove(material)
        raise
    finally:
        _initializing.pop(key, None)
    return material
