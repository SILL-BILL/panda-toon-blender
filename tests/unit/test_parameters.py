# SPDX-License-Identifier: GPL-3.0-or-later
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


parameters = load("parameters", "src/panda_toon/parameters.py")
core = load("core", "src/panda_toon/nodes/core.py")


class ParameterTests(unittest.TestCase):
    def test_threshold_bounds_and_order(self):
        self.assertEqual(parameters.ordered_thresholds(2, -1), (0, 1))
        self.assertEqual(parameters.ordered_thresholds(.8, .2), (.2, .8))
        for bad in (float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                parameters.ordered_thresholds(bad, .5)

    def test_graph_matches_piecewise_reference(self):
        # Evaluate the actual Math-node connections, independently of bpy.
        for low, high in ((.25, .65), (.5, .5), (0, 1)):
            for dark, mid, light in ((.18, .55, 1), (2, .1, .4)):
                for value in (0, low - .001, low, high - .001, high, 1, 3):
                    values = {"luma": value, "dark": dark, "mid": mid, "light": light}
                    def evaluate(role):
                        if role in values:
                            return values[role]
                        inputs = {d: evaluate(a) for a,b,c,d in core.LEGACY_EDGES if c == role}
                        if role in ("low", "high"):
                            inputs[1] = low if role == "low" else high
                        a, b = inputs[0], inputs[1]
                        op = core.LEGACY_OPERATIONS[role]
                        result = {"LESS_THAN": lambda: float(a < b),
                                  "SUBTRACT": lambda: a - b, "ADD": lambda: a + b,
                                  "MULTIPLY": lambda: a * b}[op]()
                        values[role] = result
                        return result
                    self.assertAlmostEqual(evaluate("tone"),
                        parameters.tone_at(value, low, high, dark, mid, light))

    def test_softness_is_centered_on_both_thresholds(self):
        for value, expected in ((.15, .2), (.25, .35), (.35, .5),
                                (.55, .5), (.65, .75), (.75, 1)):
            self.assertAlmostEqual(parameters.tone_at(value, .25, .65, .2, .5, 1, .2),
                                   expected)

    def test_overlapping_and_equal_thresholds(self):
        for low, high in ((.45, .55), (.5, .5), (0, 1)):
            for width in (1e-8, .3, 1):
                for value in (0, .49, .5, .51, 1, 3):
                    self.assertGreaterEqual(parameters.tone_at(value, low, high, .2, .5, 1, width),
                                            .2 - 1e-12)
                    self.assertLessEqual(parameters.tone_at(value, low, high, .2, .5, 1, width), 1)
                if low == high:
                    self.assertAlmostEqual(parameters.tone_at(low, low, high, .2, 4, 1, width), .6)

if __name__ == "__main__":
    unittest.main()
