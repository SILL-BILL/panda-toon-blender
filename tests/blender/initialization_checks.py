# SPDX-License-Identifier: GPL-3.0-or-later
"""In-memory regressions: never reads a user scene or writes a file."""
import bpy
from panda_toon.material.service import create_material
from panda_toon.nodes.core import build_new, inspect, update, TYPES, EDGES, OWNER


def snapshot(material):
    return (tuple((n.as_pointer(), n.bl_idname) for n in material.node_tree.nodes),
            tuple((l.from_socket.as_pointer(), l.to_socket.as_pointer())
                  for l in material.node_tree.links))


def run_checks():
    user = bpy.data.materials.new("PT_TestExistingUserMaterial")
    user.node_tree.nodes.new("ShaderNodeValue")
    before = snapshot(user)
    for action in (build_new, update):
        try:
            action(user)
        except ValueError:
            pass
        else:
            raise AssertionError("Existing material must be rejected")
        assert snapshot(user) == before

    plain = bpy.data.materials.new("PT_TestExistingStandardMaterial")
    plain_before = snapshot(plain)
    try:
        build_new(plain)
    except ValueError:
        pass
    else:
        raise AssertionError("Even a standard existing material must be rejected")
    assert snapshot(plain) == plain_before

    material = create_material("PT_InitializationRegression")
    nodes = inspect(material)
    assert len(material.node_tree.nodes) == len(TYPES)
    assert len(material.node_tree.links) == len(EDGES)
    assert all(n.get(OWNER) in TYPES for n in material.node_tree.nodes)
    assert not any(n.bl_idname == "ShaderNodeBsdfPrincipled" for n in material.node_tree.nodes)
    stable = snapshot(material)
    for value in (.3, .6, .9):
        material.panda_toon.mid_tone = value
        assert not material.panda_toon.last_error
        assert snapshot(material) == stable
    try:
        build_new(material)
    except ValueError:
        pass
    else:
        raise AssertionError("Initialization permission must not be reusable")
    assert snapshot(material) == stable
    material.node_tree.links.remove(material.node_tree.links[0])
    altered = snapshot(material)
    try:
        update(material)
    except ValueError:
        pass
    else:
        raise AssertionError("Edited connections must be rejected")
    assert snapshot(material) == altered
    for item in (user, plain, material):
        bpy.data.materials.remove(item)
    print("PASS: initialization and existing-material protection regressions", flush=True)
