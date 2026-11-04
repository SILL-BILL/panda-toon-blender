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
                        inputs = {d: evaluate(a) for a,b,c,d in core.EDGES if c == role}
                        if role in ("low", "high"):
                            inputs[1] = low if role == "low" else high
                        a, b = inputs[0], inputs[1]
                        op = core.OPERATIONS[role]
                        result = {"LESS_THAN": lambda: float(a < b),
                                  "SUBTRACT": lambda: a - b, "ADD": lambda: a + b,
                                  "MULTIPLY": lambda: a * b}[op]()
                        values[role] = result
                        return result
                    self.assertAlmostEqual(evaluate("tone"),
                        parameters.tone_at(value, low, high, dark, mid, light))


if __name__ == "__main__":
    unittest.main()
