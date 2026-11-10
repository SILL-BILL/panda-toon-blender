# SPDX-License-Identifier: GPL-3.0-or-later
"""APPROVAL REQUIRED: isolated Blender integration and render test."""
import math
from array import array
from pathlib import Path
import sys
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lab_support import report, setup

import panda_toon
from panda_toon.material.service import create_material
from panda_toon.nodes.core import (
    EDGES, LEGACY_EDGES, LEGACY_TYPES, LEGACY_VERSION, OWNER, SCHEMA, TYPES,
    inspect, update,
)


def review_softness_scene(run):
    scene_path = run / "scenes/softness-review.blend"
    assert bpy.ops.wm.open_mainfile(filepath=str(scene_path), load_ui=False,
                                  use_scripts=False) == {"FINISHED"}
    sphere = bpy.context.scene.objects["PT_SoftnessSphere"]
    inspect(sphere.active_material)
    view_layer = bpy.context.view_layer
    sphere.select_set(True)
    view_layer.objects.active = sphere
    for area in bpy.context.window_manager.windows[0].screen.areas:
        if area.type == "PROPERTIES":
            area.spaces.active.context = "MATERIAL"
        elif area.type == "VIEW_3D":
            area.spaces.active.shading.type = "RENDERED"
            area.spaces.active.region_3d.view_perspective = "CAMERA"


def check_softness(run, sphere, material, render):
    settings = material.panda_toon
    nodes = inspect(material)
    stable = {role: node.as_pointer() for role, node in nodes.items()}
    for width in (0, 1e-8, 0.3, 1):
        settings.shadow_edge_softness = width
        settings.threshold_high = settings.threshold_low
        assert not settings.last_error, settings.last_error
        for role in ("low", "high"):
            assert nodes[f"{role}_select"].inputs[0].default_value == float(width > 0)
            bounds = nodes[f"{role}_smooth"].inputs
            assert bounds[1].default_value < 0 < bounds[2].default_value
        assert stable == {role: node.as_pointer() for role, node in inspect(material).items()}
    settings.threshold_high = .65
    settings.shadow_edge_softness = 0

    # Reconstruct the old graph on a disposable copy using the unchanged schema 1 contract.
    legacy = material.copy()
    legacy.name = "PT_Schema1_Reference"
    legacy_nodes = inspect(legacy)
    for role in TYPES.keys() - LEGACY_TYPES.keys():
        assert legacy_nodes[role].get(OWNER) == role
        legacy.node_tree.nodes.remove(legacy_nodes[role])
    for a, b, c, d in LEGACY_EDGES:
        if (a, b, c, d) not in EDGES:
            legacy.node_tree.links.new(legacy_nodes[a].outputs[b], legacy_nodes[c].inputs[d])
    legacy[SCHEMA] = LEGACY_VERSION
    old_nodes = inspect(legacy)
    legacy.panda_toon.threshold_low = .2
    assert math.isclose(old_nodes["low"].inputs[1].default_value, .2, abs_tol=1e-6)
    legacy.panda_toon.threshold_low = settings.threshold_low
    assert not legacy.panda_toon.last_error, legacy.panda_toon.last_error
    assert inspect(legacy) == old_nodes

    def pixels(path):
        image = bpy.data.images.load(str(path), check_existing=False)
        try:
            result = array("f", [0]) * len(image.pixels)
            image.pixels.foreach_get(result)
            return result
        finally:
            bpy.data.images.remove(image)

    sphere.data.materials[0] = legacy
    baseline = pixels(render("schema1-hard-reference"))
    sphere.data.materials[0] = material
    previous = baseline
    for width in (0.00, 0.05, 0.15, 0.30):
        settings.shadow_edge_softness = width
        current = pixels(render(f"softness-{width:.2f}"))
        assert (current == previous) == (width == 0), width
        previous = current

    settings.shadow_edge_softness = .15
    material_name = material.name
    blend_path = run / "scenes/softness.blend"
    assert not blend_path.exists()
    assert bpy.ops.wm.save_as_mainfile(filepath=str(blend_path), check_existing=True) == {"FINISHED"}
    assert bpy.ops.wm.open_mainfile(filepath=str(blend_path), load_ui=False,
                                  use_scripts=False) == {"FINISHED"}
    restored = bpy.data.materials[material_name]
    assert math.isclose(restored.panda_toon.shadow_edge_softness, .15, abs_tol=1e-6)
    assert inspect(restored)["low_select"].inputs[0].default_value == 1
    restored.panda_toon.shadow_edge_softness = 0
    assert not restored.panda_toon.last_error
    assert inspect(restored)["low_select"].inputs[0].default_value == 0


def main():
    run, stage, identity = setup()
    assert stage in ("structure", "first", "remaining", "save", "softness", "softness-gui")
    outputs = {name: run / name for name in ("scenes", "renders")}
    panda_toon.register()
    if stage == "softness-gui":
        review_softness_scene(run)
        report(run, stage, identity, manual_result="pending")
        return
    panda_toon.unregister()
    panda_toon.register()
    sys.path.insert(0, str(ROOT / "tests/blender"))
    from initialization_checks import run_checks
    run_checks()
    material = create_material()
    nodes = inspect(material)
    assert len(nodes) == len(TYPES)
    pointers = {key: node.as_pointer() for key, node in nodes.items()}
    p = material.panda_toon
    p.threshold_low = .9
    assert p.threshold_low == p.threshold_high
    p.threshold_low = .25
    p.threshold_high = .1
    assert p.threshold_high == p.threshold_low
    p.threshold_high = .65
    p.base_color = (.2, .5, .8, 1)
    p.dark_tone = .2
    for _ in range(5):
        update(material)
    assert pointers == {key: node.as_pointer() for key, node in inspect(material).items()}
    assert abs(nodes["dark"].outputs[0].default_value - .2) < 1e-6
    assert abs(nodes["base"].outputs[0].default_value[1] - .5) < 1e-6
    user_node = material.node_tree.nodes.new("ShaderNodeValue")
    update(material)
    assert user_node in list(material.node_tree.nodes)
    link = next(link for link in material.node_tree.links if link.to_node == nodes["emission"])
    material.node_tree.links.remove(link)
    before = len(material.node_tree.nodes)
    try:
        update(material)
    except ValueError:
        pass
    else:
        raise AssertionError("Modified graph must be rejected")
    assert len(material.node_tree.nodes) == before
    material.node_tree.links.new(nodes["shade"].outputs[0], nodes["emission"].inputs[0])
    image = bpy.data.images.new("PT_Checker", width=8, height=8)
    image.pixels = [v for y in range(8) for x in range(8)
                    for v in ((1, .3, .1, 1) if (x+y)%2 else (.1, .7, 1, 1))]
    image.pack()
    p.texture = image
    assert nodes["texture"].image == image
    assert nodes["tint"].inputs[0].default_value == 1
    p.texture = None
    assert nodes["tint"].inputs[0].default_value == 0

    assert not p.last_error, p.last_error
    if stage == "structure":
        panda_toon.unregister()
        report(run, stage, identity)
        return

    # Only the factory scene in this disposable process is cleared.
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 512
    scene.render.resolution_y = 512
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = 0
    scene.view_settings.gamma = 1
    scene.world.use_nodes = True
    scene.world.node_tree.nodes.get("Background").inputs[1].default_value = 0
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, location=(-1.3, 0, 1))
    sphere = bpy.context.object
    sphere.data.materials.append(material)
    for poly in sphere.data.polygons:
        poly.use_smooth = True
    bpy.ops.mesh.primitive_cube_add(size=1.5, location=(1.2, .2, .75))
    bpy.context.object.data.materials.append(material)
    bpy.ops.mesh.primitive_plane_add(size=200)
    floor = create_material("PT_Floor")
    floor.panda_toon.base_color = (.7, .7, .7, 1)
    bpy.context.object.data.materials.append(floor)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 2, 1.5))
    bpy.context.object.name = "PT_Occluder"
    bpy.context.object.data.materials.append(floor)
    bpy.ops.object.light_add(type="SUN", location=(0, 0, 6))
    sun = bpy.context.object
    sun.data.energy = 3
    sun.data.angle = math.radians(1)
    sun.rotation_euler = (math.radians(25), math.radians(-35), math.radians(-30))
    bpy.ops.object.camera_add(location=(6, -10, 7))
    camera = bpy.context.object
    camera.rotation_euler = (Vector((0, 0, 1)) - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 7
    scene.camera = camera

    def render(name):
        assert not p.last_error, p.last_error
        destination = outputs["renders"] / (name + ".png")
        assert not destination.exists()
        scene.render.filepath = str(destination)
        assert bpy.ops.render.render(write_still=True) == {"FINISHED"}
        with destination.open("rb") as stream:
            assert stream.read(8) == b"\x89PNG\r\n\x1a\n"
        assert destination.stat().st_size > 100
        return destination

    if stage == "softness":
        sphere.name = "PT_SoftnessSphere"
        camera.rotation_euler = (sphere.location - camera.location).to_track_quat("-Z", "Y").to_euler()
        camera.data.ortho_scale = 3.2
        check_softness(run, sphere, material, render)
        panda_toon.unregister()
        report(run, stage, identity, zero_matches_schema1=True, saved_softness=.15)
        return
    if stage == "first":
        render("01-base")
    else:
        sun.rotation_euler.z += math.radians(90)
        if stage == "remaining":
            render("02-light-direction")
        p.threshold_low, p.threshold_high = .4, .8
        if stage == "remaining":
            render("03-thresholds")
        p.base_color = (.8, .2, .1, 1)
        if stage == "remaining":
            render("04-base-color")
        p.texture = image
        if stage == "remaining":
            render("05-texture")
        p.mid_tone = .7
        if stage == "remaining":
            render("06-tone-multiplier")

    if stage != "save":
        panda_toon.unregister()
        report(run, stage, identity)
        return

    material_name = material.name
    blend_path = outputs["scenes"] / "phase1a.blend"
    assert not blend_path.exists()
    assert bpy.context.preferences.filepaths.file_preview_type == "NONE"
    assert bpy.ops.wm.save_as_mainfile(filepath=str(blend_path), check_existing=True) == {"FINISHED"}
    assert bpy.ops.wm.open_mainfile(filepath=str(blend_path), load_ui=False, use_scripts=False) == {"FINISHED"}
    restored = bpy.data.materials[material_name]
    assert restored.panda_toon.texture is not None
    assert abs(restored.panda_toon.threshold_high - .8) < 1e-6
    assert abs(restored.panda_toon.base_color[0] - .8) < 1e-6
    inspect(restored)
    assert abs(restored.panda_toon.mid_tone - .7) < 1e-6
    panda_toon.unregister()
    report(run, stage, identity)


if __name__ == "__main__":
    main()
