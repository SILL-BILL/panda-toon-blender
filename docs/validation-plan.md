# Blender CLI execution proposal — NOT YET APPROVED

## Command

From the project root, after explicit approval:

```powershell
powershell -NoProfile -File .\tools\run_blender_tests.ps1
```

The wrapper generates a UUID run ID and launches exactly this command with
absolute project paths and that ID substituted:

```text
"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe" --background --factory-startup --disable-autoexec --python-exit-code 1 --python "D:\dev-blender-addon\panda-toon-blender\tests\blender\phase1a.py" -- phase1a-<UUID>
```

The complete scripts are tools/run_blender_tests.ps1 and tests/blender/phase1a.py.
Read them as the reviewable execution specification. The wrapper sets process-only
BLENDER_USER_RESOURCES/CONFIG/SCRIPTS/EXTENSIONS/DATAFILES, TEMP/TMP and disables
bytecode writes, then restores the previous environment in finally.

## Inputs / actions

Reads installed Blender runtime, project Python modules and this test script.
Starts with the factory scene; never opens an existing user blend. Registers,
unregisters and re-registers the extension in memory. Asserts node ownership,
connections, thresholds, input updates, stable node identity, texture switching
and rejection of edited graphs. Builds a sphere/cube/floor/occluder/sun/camera
scene and an internal packed checker image; no external image input.

Renders six PNGs for base, changed light, thresholds, color, texture, and reload.
Saves a newly generated scene and reopens only that scene with scripts disabled.
Checks persisted settings and unregisters. Reports failures through nonzero exit.

## Outputs (all relative to this project)

- `lab/temp/phase1a-<UUID>/`: isolated process settings and temporary locations.
- `lab/scenes/phase1a-<UUID>/phase1a.blend`: new test scene, never overwrite.
- `lab/renders/phase1a-<UUID>/01-base.png` through `06-reloaded.png`.
- `lab/logs/phase1a-<UUID>/results.json`: version, rendering conditions and test status.
- Console output; failures may leave partial artifacts for diagnosis.

No preference save, addon installation, network request, commit or push is requested.
Potential risks: GPU/CPU/memory load, driver crash/cache writes, Blender-version API
failures, and partial test outputs. This is process/config isolation, not a sandbox
guaranteeing no access to the rest of the machine.

## Acceptance after this run

User must inspect three tones, moving/occlusion shadows, threshold area, color and
texture changes. There is no approved baseline yet. This script tests module
registration and same-process reload, not actual Extension installation or a fresh
Blender restart. ZIP installation/enabling, realtime UI, parameter editing and
restart persistence need a subsequent approved manual validation session.
