# SPDX-License-Identifier: GPL-3.0-or-later
"""Callback contract/recursion tests without importing the Blender runtime."""
import importlib.util
import inspect
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch


def load_settings():
    bpy = ModuleType("bpy")
    bpy.types = SimpleNamespace(PropertyGroup=object, Image=object)
    props = ModuleType("bpy.props")
    for name in ("FloatProperty", "FloatVectorProperty", "PointerProperty", "StringProperty"):
        setattr(props, name, lambda **kwargs: kwargs)
    core = ModuleType("callback_tests.nodes.core")
    core.SCHEMA = "panda_toon_schema"
    core.VERSION = 2
    core.update = Mock()
    path = Path(__file__).resolve().parents[2] / "src/panda_toon/material/settings.py"
    spec = importlib.util.spec_from_file_location("callback_tests.material.settings", path)
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {"bpy": bpy, "bpy.props": props,
                                 "callback_tests.nodes.core": core}):
        spec.loader.exec_module(module)
    return module


class CallbackTests(unittest.TestCase):
    def setUp(self):
        self.module = load_settings()
        class Material(dict):
            def as_pointer(self):
                return 123
        self.material = Material(panda_toon_schema=1)
        self.settings = SimpleNamespace(id_data=self.material, threshold_low=.25,
                                       threshold_high=.65, last_error="")

    def test_every_registered_update_has_exactly_two_arguments(self):
        callbacks = [v["update"] for v in self.module.PandaToonSettings.__annotations__.values()
                     if "update" in v]
        self.material["panda_toon_schema"] = 2
        self.assertEqual(len(callbacks), 8)
        for callback in callbacks:
            with self.subTest(callback=callback.__name__):
                self.assertEqual(callback.__code__.co_argcount, 2)
                self.assertEqual(list(inspect.signature(callback).parameters), ["self", "context"])
                self.assertIsNone(callback.__defaults__)
                callback(self.settings, None)
        self.assertEqual(self.module.update.call_count, 8)

    def test_softness_callback_leaves_schema_one_alone(self):
        self.module.changed_softness(self.settings, None)
        self.module.update.assert_not_called()

    def test_threshold_callbacks_clamp_only_edited_threshold(self):
        self.settings.threshold_low = .9
        self.module.changed_low(self.settings, None)
        self.assertEqual((self.settings.threshold_low, self.settings.threshold_high), (.65, .65))
        self.settings.threshold_high = .1
        self.module.changed_high(self.settings, None)
        self.assertEqual((self.settings.threshold_low, self.settings.threshold_high), (.65, .65))

    def test_reentrant_update_runs_once_and_guard_is_released_after_error(self):
        self.module.update.side_effect = lambda mat: self.module.changed(self.settings, None)
        self.module.changed(self.settings, None)
        self.module.update.assert_called_once_with(self.material)
        self.assertEqual(self.module._updating, set())
        self.module.update.side_effect = ValueError("edited graph")
        self.module.changed(self.settings, None)
        self.assertEqual(self.settings.last_error, "edited graph")
        self.assertEqual(self.module._updating, set())
        self.module.update.side_effect = None
        self.module.changed(self.settings, None)
        self.assertEqual(self.settings.last_error, "")


if __name__ == "__main__":
    unittest.main()
