# SPDX-License-Identifier: GPL-3.0-or-later
"""APPROVAL REQUIRED: isolated Blender integration and render test."""
import math
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
from panda_toon.nodes.core import inspect, update, TYPES


def main():
    run, stage, identity = setup()
    assert stage in ("structure", "first", "remaining", "save")
    outputs = {name: run / name for name in ("scenes", "renders")}
    panda_toon.register()
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
