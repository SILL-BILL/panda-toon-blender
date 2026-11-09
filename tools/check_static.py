# SPDX-License-Identifier: GPL-3.0-or-later
"""Parse all Python/TOML without importing bpy or generating bytecode."""
import ast
from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parents[1]
paths = [p for folder in ("src", "tests", "tools") for p in (ROOT / folder).rglob("*.py")]
for path in paths:
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
manifest = tomllib.loads((ROOT / "src/panda_toon/blender_manifest.toml").read_text())
assert manifest["license"] == ["SPDX:GPL-3.0-or-later"]
assert manifest["blender_version_min"] == "5.1.0"
assert manifest["blender_version_max"] == "5.3.0"
assert "GNU GENERAL PUBLIC LICENSE" in (ROOT / "LICENSE").read_text()
assert "GNU AFFERO GENERAL PUBLIC LICENSE" not in (ROOT / "LICENSE").read_text()
print(f"PASS: {len(paths)} Python files parsed; manifest/license checks passed")
