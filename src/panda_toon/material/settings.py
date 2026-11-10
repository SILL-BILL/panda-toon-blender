# SPDX-License-Identifier: GPL-3.0-or-later
import bpy
from bpy.props import FloatProperty, FloatVectorProperty, PointerProperty, StringProperty
from ..nodes.core import SCHEMA, VERSION, update

_updating = set()


def _apply_change(self, context, edited=None):
    material = self.id_data
    key = material.as_pointer()
    if key in _updating or SCHEMA not in material:
        return
    _updating.add(key)
    try:
        if self.threshold_low > self.threshold_high:
            if edited == "low":
                self.threshold_low = self.threshold_high
            else:
                self.threshold_high = self.threshold_low
        update(material)
        self.last_error = ""
    except (ValueError, RuntimeError, TypeError) as exc:
        self.last_error = str(exc)
    finally:
        _updating.discard(key)


def changed(self, context):
    _apply_change(self, context)


def changed_low(self, context):
    _apply_change(self, context, "low")


def changed_high(self, context):
    _apply_change(self, context, "high")


def changed_softness(self, context):
    if self.id_data.get(SCHEMA) == VERSION:
        _apply_change(self, context)


class PandaToonSettings(bpy.types.PropertyGroup):
    base_color: FloatVectorProperty(name="Base Color", subtype="COLOR", size=4,
        min=0, max=1, default=(0.65, 0.25, 0.12, 1), update=changed)
    texture: PointerProperty(name="Base Color Texture", type=bpy.types.Image, update=changed)
    threshold_low: FloatProperty(name="Shadow Threshold 1", min=0, max=1, default=0.25,
        update=changed_low)
    threshold_high: FloatProperty(name="Shadow Threshold 2", min=0, max=1, default=0.65,
        update=changed_high)
    shadow_edge_softness: FloatProperty(name="Shadow Edge Softness", min=0, max=1,
        default=0, precision=2, description="Luminance transition width around both shadow thresholds",
        update=changed_softness)
    light_tone: FloatProperty(name="Light Tone", min=0, max=4, default=1, update=changed)
    mid_tone: FloatProperty(name="Mid Tone", min=0, max=4, default=0.55, update=changed)
    dark_tone: FloatProperty(name="Dark Tone", min=0, max=4, default=0.18, update=changed)
    last_error: StringProperty(options={"SKIP_SAVE"})
