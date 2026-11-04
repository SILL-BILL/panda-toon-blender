# SPDX-License-Identifier: GPL-3.0-or-later
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from test_parameters import core


class Node(dict):
    def __init__(self, kind):
        super().__init__()
        self.bl_idname = kind
        self.inputs = [object()]
        self.outputs = [object()]
        self.mute = False
        self.is_active_output = True
        self.target = "ALL"


class Material(dict):
    users = 0
    animation_data = None

    def as_pointer(self):
        return id(self)


def standard_material():
    material = Material()
    bsdf, output = Node("ShaderNodeBsdfPrincipled"), Node("ShaderNodeOutputMaterial")
    material.node_tree = SimpleNamespace(nodes=[bsdf, output], animation_data=None,
        links=[SimpleNamespace(from_socket=bsdf.outputs[0], to_socket=output.inputs[0])])
    return material


class InitializationTests(unittest.TestCase):
    def test_expected_standard_graph_is_accepted_without_mutation(self):
        material = standard_material()
        nodes = tuple(material.node_tree.nodes)
        self.assertEqual(core._standard_nodes(material), nodes)
        self.assertEqual(tuple(material.node_tree.nodes), nodes)

    def test_unexpected_graphs_are_rejected_without_mutation(self):
        def extra(m): m.node_tree.nodes.append(Node("ShaderNodeValue"))
        def disconnected(m): m.node_tree.links.clear()
        def wrong_socket(m): m.node_tree.links[0].to_socket = object()
        def custom_property(m): m.node_tree.nodes[0].__setitem__("user", True)
        def used(m): m.users = 1
        def missing(m): m.node_tree = None
        for mutation in (extra, disconnected, wrong_socket, custom_property, used, missing):
            with self.subTest(mutation=mutation.__name__):
                material = standard_material()
                mutation(material)
                tree = material.node_tree
                nodes = tuple(tree.nodes) if tree else None
                with self.assertRaises(ValueError): core._standard_nodes(material)
                self.assertIs(material.node_tree, tree)
                self.assertEqual(tuple(tree.nodes) if tree else None, nodes)

    def test_creation_permission_is_scoped_and_consumed_once(self):
        allocated = standard_material()
        materials = SimpleNamespace(new=Mock(return_value=allocated), remove=Mock())
        path = Path(__file__).resolve().parents[2] / "src/panda_toon/material/service.py"
        spec = importlib.util.spec_from_file_location("init_tests.material.service", path)
        service = importlib.util.module_from_spec(spec)
        builder = Mock()
        with patch.dict(sys.modules, {"bpy": SimpleNamespace(data=SimpleNamespace(materials=materials)),
                                      "init_tests.nodes.core": SimpleNamespace(build_new=builder)}):
            spec.loader.exec_module(service)
        existing = standard_material()
        with self.assertRaises(ValueError): service._claim_new_material(existing)
        def build(material):
            self.assertIs(material, allocated)
            service._claim_new_material(material)
            with self.assertRaises(ValueError): service._claim_new_material(material)
        builder.side_effect = build
        self.assertIs(service.create_material(), allocated)
        self.assertEqual(service._initializing, {})
        materials.remove.assert_not_called()
        with self.assertRaises(ValueError): service._claim_new_material(allocated)
        builder.side_effect = ValueError("unexpected defaults")
        with self.assertRaises(ValueError): service.create_material()
        materials.remove.assert_called_once_with(allocated)
        self.assertEqual(service._initializing, {})


if __name__ == "__main__":
    unittest.main()
