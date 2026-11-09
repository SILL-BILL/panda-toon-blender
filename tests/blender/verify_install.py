# SPDX-License-Identifier: GPL-3.0-or-later
# Installed-package verification only; never imports the product source tree.
import bpy
import addon_utils
import importlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import hashlib
import tomllib
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lab_support import ROOT, report, setup

RUN, MODE, identity = setup()
assert MODE in ('install', 'restart', 'gui', 'gui-retry')
gui = MODE in ('gui', 'gui-retry')
MODULE = 'bl_ext.panda_lab.panda_toon'
CONFIG = RUN / 'env/BLENDER_USER_CONFIG'
REPO = RUN / 'env/BLENDER_USER_EXTENSIONS/panda_lab'
ZIP = RUN / 'panda_toon.zip'
SCENE = RUN / 'scenes/installed-scene.blend'
prefs = bpy.context.preferences

source = ROOT / 'src/panda_toon'
expected_files = {
    path.relative_to(source).as_posix(): path.read_bytes()
    for path in source.rglob('*')
    if path.is_file() and path.suffix in ('.py', '.toml', '.md')
}
expected_files['LICENSE'] = (ROOT / 'LICENSE').read_bytes()
with ZipFile(ZIP) as archive:
    assert sorted(archive.namelist()) == sorted(expected_files)
    assert all(archive.read(name) == data for name, data in expected_files.items())
manifest = tomllib.loads(expected_files['blender_manifest.toml'].decode())
assert manifest['id'] == 'panda_toon'
assert manifest['license'] == ['SPDX:GPL-3.0-or-later']
assert manifest['blender_version_min'] == '5.1.0'
assert manifest['blender_version_max'] == '5.3.0'
zip_sha256 = hashlib.sha256(ZIP.read_bytes()).hexdigest()
print(f"ZIP SHA-256: {zip_sha256}; repository: {REPO}", flush=True)

if MODE == 'install':
    assert not (CONFIG / 'userpref.blend').exists()
    assert not REPO.exists()
    for repo in prefs.extensions.repos:
        repo.enabled = False
    repo = prefs.extensions.repos.new(name='Panda Toon Lab', module='panda_lab',
        custom_directory=str(REPO), remote_url='', source='USER')
    assert repo.module == 'panda_lab' and Path(repo.directory).resolve() == REPO.resolve()
    assert repo.enabled and not repo.remote_url
    result = bpy.ops.extensions.package_install_files('EXEC_DEFAULT', filepath=str(ZIP),
        repo=repo.module, enable_on_install=True)
    assert result == {'FINISHED'}, result
else:
    # Do not enable/re-register here: these checks must pass from saved preferences.
    assert (CONFIG / 'userpref.blend').is_file()
    initial = json.loads((RUN / 'logs/install.json').read_text())
    assert initial['zip_sha256'] == zip_sha256
    assert initial['build_hash'] == identity['build_hash']
    assert initial['pid'] != os.getpid(), 'Must be a distinct process'
    repo = next(r for r in prefs.extensions.repos if r.module == 'panda_lab')
    assert repo.enabled and not repo.remote_url
    assert Path(repo.directory).resolve() == REPO.resolve()

installed = REPO / 'panda_toon'
assert installed.is_dir(), f'Package missing after operation: {installed}'
actual_files = {p.relative_to(installed).as_posix() for p in installed.rglob('*') if p.is_file()}
allowed_caches = {
    Path(importlib.util.cache_from_source(str(installed / name))).relative_to(installed).as_posix()
    for name in expected_files if name.endswith('.py')
}
missing = set(expected_files) - actual_files
unexpected = actual_files - set(expected_files) - allowed_caches
assert not missing and not unexpected, (sorted(missing), sorted(unexpected))
for name, data in expected_files.items():
    assert (installed / name).read_bytes() == data, name

assert MODULE in prefs.addons
assert addon_utils.check(MODULE) == (True, True), addon_utils.check(MODULE)
assert MODULE in sys.modules, 'Expected automatic registration'
addon = importlib.import_module(MODULE)
assert Path(addon.__file__).resolve() == (REPO / 'panda_toon/__init__.py').resolve()
assert all(cls.is_registered for cls in addon.CLASSES)
assert hasattr(bpy.types.Material, 'panda_toon')
core = importlib.import_module(MODULE + '.nodes.core')
if gui:
    scene = RUN / 'scenes' / ('gui-review-retry.blend' if MODE == 'gui-retry' else 'gui-review.blend')
    assert bpy.ops.wm.open_mainfile(filepath=str(scene), load_ui=False, use_scripts=False) == {'FINISHED'}
    assert prefs.filepaths.file_preview_type == 'NONE' and not prefs.use_preferences_save
    sphere = bpy.context.scene.objects['Sphere']
    core.inspect(sphere.active_material)
    settings = sphere.active_material.panda_toon
    settings.texture = None
    settings.base_color = (.2, .5, .8, 1)
    settings.threshold_low = .25
    settings.threshold_high = .65
    settings.light_tone, settings.mid_tone, settings.dark_tone = 1, .55, .2
    assert not settings.last_error, settings.last_error
    window = bpy.context.window or bpy.context.window_manager.windows[0]
    view_layer = window.view_layer
    for obj in view_layer.objects:
        if obj.select_get(view_layer=view_layer):
            obj.select_set(False, view_layer=view_layer)
    sphere.select_set(True, view_layer=view_layer)
    view_layer.objects.active = sphere
    for area in window.screen.areas:
        if area.type == 'PROPERTIES':
            area.spaces.active.context = 'MATERIAL'
        elif area.type == 'VIEW_3D':
            area.spaces.active.shading.type = 'RENDERED'
            area.spaces.active.region_3d.view_perspective = 'CAMERA'
    report(RUN, MODE, identity, zip_sha256=zip_sha256, manual_result='pending')

# Exercise operator and UI properties in background mode. Visual layout is not claimed.
def exercise_ui():
    bpy.context.scene.render.engine = 'BLENDER_EEVEE'
    bpy.ops.mesh.primitive_cube_add()
    obj = bpy.context.object
    previous = len(obj.data.materials)
    assert bpy.ops.panda_toon.create_material.poll()
    assert bpy.ops.panda_toon.create_material() == {'FINISHED'}
    assert len(obj.data.materials) == previous + 1
    mat = obj.active_material
    nodes = core.inspect(mat)
    stable = {k:n.as_pointer() for k,n in nodes.items()}
    p = mat.panda_toon
    p.base_color = (.2,.3,.4,1)
    p.threshold_low = .45
    p.threshold_high = .8
    p.mid_tone = .64
    assert not p.last_error, p.last_error
    assert abs(nodes['mid'].outputs[0].default_value - .64) < 1e-6
    assert abs(nodes['low'].inputs[1].default_value - .45) < 1e-6
    assert stable == {k:n.as_pointer() for k,n in core.inspect(mat).items()}
    class LayoutRecorder:
        def __init__(self): self.properties = []; self.operators = []
        def operator(self, name, **kwargs): self.operators.append(name)
        def label(self, **kwargs): pass
        def column(self): return self
        def prop(self, data, name):
            assert hasattr(data, name)
            self.properties.append(name)
    from types import SimpleNamespace
    layout = LayoutRecorder()
    panel = addon.CLASSES[-1]
    panel.draw(SimpleNamespace(layout=layout),
               SimpleNamespace(scene=bpy.context.scene, material=mat))
    assert layout.operators == ['panda_toon.create_material']
    assert layout.properties == ['base_color','texture','threshold_low','threshold_high',
                                 'light_tone','mid_tone','dark_tone']
    return mat, layout.properties

if not gui:
    material, properties = exercise_ui()
    details = {'mode':MODE, 'pid':os.getpid(), 'blender':bpy.app.version_string,
        'offline':not bpy.app.online_access, 'module':MODULE, 'module_file':addon.__file__,
        'enabled':True, 'installed_bytes_match_zip':True, 'material_creation':'passed',
        'registered_ui_properties':properties, 'ui_operator_and_callbacks':'passed',
        'headless_panel_draw_contract':'passed', 'visual_gui_interaction':'not tested',
        'config_directory':str(CONFIG), 'repository':str(REPO)}
    if MODE == 'install':
        assert not SCENE.exists()
        bpy.context.scene['panda_install_material'] = material.name
        assert prefs.filepaths.file_preview_type == 'NONE'
        assert bpy.ops.wm.save_as_mainfile(filepath=str(SCENE), check_existing=True) == {'FINISHED'}
        assert SCENE.is_file()
        assert Path(bpy.utils.user_resource('CONFIG')).resolve() == CONFIG.resolve()
        assert bpy.ops.wm.save_userpref() == {'FINISHED'}
        assert (CONFIG / 'userpref.blend').is_file()
        details['scene_saved'] = str(SCENE)
    else:
        assert SCENE.is_file()
        assert bpy.ops.wm.open_mainfile(filepath=str(SCENE), load_ui=False, use_scripts=False) == {'FINISHED'}
        assert prefs.filepaths.file_preview_type == 'NONE'
        restored = bpy.data.materials[bpy.context.scene['panda_install_material']]
        core.inspect(restored)
        p = restored.panda_toon
        assert abs(p.threshold_low-.45)<1e-6 and abs(p.threshold_high-.8)<1e-6
        assert abs(p.mid_tone-.64)<1e-6 and abs(p.base_color[1]-.3)<1e-6
        p.dark_tone = .22
        assert not p.last_error
        assert abs(core.inspect(restored)['dark'].outputs[0].default_value-.22)<1e-6
        details['saved_scene_and_callbacks_after_restart'] = 'passed'
    report(RUN, MODE, identity, zip_sha256=zip_sha256, files=sorted(expected_files), **details)
