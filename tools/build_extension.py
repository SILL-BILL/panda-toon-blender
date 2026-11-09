# SPDX-License-Identifier: GPL-3.0-or-later
"""Create a new ZIP without installing anything or overwriting an archive."""
from pathlib import Path
import tomllib
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def build(output=None):
    source = ROOT / "src/panda_toon"
    manifest = tomllib.loads((source / "blender_manifest.toml").read_text())
    output = output or ROOT / "dist" / f"panda_toon-{manifest['version']}.zip"
    output.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(output, "x", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source.rglob("*")):
            if path.is_file() and path.suffix in (".py", ".toml", ".md"):
                archive.write(path, path.relative_to(source))
        archive.write(ROOT / "LICENSE", "LICENSE")
    print(output)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    build(parser.parse_args().output)
