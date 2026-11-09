# SPDX-License-Identifier: GPL-3.0-or-later
"""Shared safeguards for the approved Phase 1A Lab entry points."""
import json
import os
from pathlib import Path
import sys
from uuid import UUID

import bpy

ROOT = Path(__file__).resolve().parents[2]


def setup():
    directory, stage, version = sys.argv[sys.argv.index("--") + 1:]
    run = Path(directory).resolve()
    assert run.parent == ROOT / "lab" / "temp"
    assert run.name == f"migration-{UUID(hex=run.name.removeprefix('migration-')).hex}"
    assert version in ("5.1.1", "5.2.3")
    assert bpy.app.version == tuple(map(int, version.split("."))), bpy.app.version_string
    assert bpy.app.background == (stage not in ("gui", "gui-retry"))
    assert not bpy.app.online_access
    for key in ("CONFIG", "SCRIPTS", "DATAFILES"):
        expected = run / "env" / ("BLENDER_USER_" + key)
        assert Path(bpy.utils.user_resource(key)).resolve() == expected
    for key in ("BLENDER_USER_RESOURCES", "BLENDER_USER_EXTENSIONS", "TEMP", "TMP"):
        assert Path(os.environ[key]).resolve() == run / "env" / key
    assert Path(bpy.app.tempdir).resolve().is_relative_to(run / "env")
    prefs = bpy.context.preferences
    prefs.use_preferences_save = False
    prefs.filepaths.use_auto_save_temporary_files = False
    prefs.filepaths.file_preview_type = "NONE"
    prefs.filepaths.save_version = 0
    identity = {
        "version": list(bpy.app.version),
        "version_string": bpy.app.version_string,
        "build_hash": bpy.app.build_hash.decode(),
        "build_branch": bpy.app.build_branch.decode(),
        "build_date": bpy.app.build_date.decode(),
        "build_time": bpy.app.build_time.decode(),
        "pid": os.getpid(),
    }
    if stage != "structure":
        baseline = json.loads((run / "logs/structure.json").read_text(encoding="utf-8"))
        assert all(identity[key] == baseline[key] for key in identity if key != "pid")
    print(json.dumps(identity), flush=True)
    return run, stage, identity


def report(run, stage, identity, **details):
    with (run / "logs" / f"{stage}.json").open("x", encoding="utf-8") as stream:
        json.dump({**identity, **details}, stream, indent=2)
    print(f"PASS: {stage}", flush=True)
