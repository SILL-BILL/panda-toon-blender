# panda-toon-blender

Panda Toon is an independently implemented three-zone toon material Extension
for Blender EEVEE. Phase 1A validation targets Blender **5.2.3 LTS**,
with 5.1.1 retained as the comparison baseline.

License: **GNU GPL v3.0 or later**, SPDX `GPL-3.0-or-later`; see [LICENSE](LICENSE).
The project owner approved replacing the initial AGPL license on 2026-10-25.

**WIP.** On Blender 5.2.3 LTS (build `e13b728c6880`), six renders, scene
save/reload and isolated GUI startup passed. Manual GUI parameter checks and
formal Phase 1A acceptance are pending. One fresh installation succeeded.
A subsequent fresh attempt failed with Windows `WinError 5` during directory rename.

See [the current validation record](docs/phase1a-52-validation.md) for evidence,
remaining issues and next steps. No external Python packages are required.

After validation and installation, open Material Properties on a mesh and choose
**New Panda Toon Material**. Existing slots and face assignments are preserved;
assign the new material to faces yourself if the mesh already has materials.
Use EEVEE and Rendered viewport shading with scene lighting. Set Base Color,
an optional existing Image datablock, two shadow thresholds, and three tone
multipliers. Texture RGB multiplies Base Color; texture alpha is not used.

Static checks (no Blender launch):

```powershell
python -B tools/check_static.py
python -B -m unittest discover -s tests/unit -v
```

Build a new ZIP with `python -B tools/build_extension.py` (refuses overwrite).
This WIP contains no ZIPs, lab scenes, renders, caches or raw logs.
Blender execution and installation require separate approval. Use the
[staged procedure](docs/phase1a-52-validation.md). The
[5.1.1 handoff](docs/handoff-2026-11-04.md) describes the earlier baseline.
