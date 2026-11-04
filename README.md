# panda-toon-blender

Panda Toon is an independently implemented three-zone toon material Extension
for Blender 5.1 EEVEE. Phase 1A targets Blender **5.1.1**.

License: **GNU GPL v3.0 or later**, SPDX `GPL-3.0-or-later`; see [LICENSE](LICENSE).
The project owner approved replacing the initial AGPL license on 2026-10-25.

Status: **WIP handoff, 2026-11-04 — not a completed release.** Blender 5.1.1
structural/render/save-reload and isolated Extension installation/restart tests
passed in prior approved runs. Rendering has provisional user acceptance.
**Manual GUI verification is incomplete:** GUI startup installation reported
`Package was expected to be installed but not found: panda_toon`; the subsequent
enabled-state assertion failed. The cause is not yet established.

Start with [the current handoff notes](docs/handoff-2026-11-04.md) for known issues,
evidence scope and next steps. No external Python packages are required.

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
**Do not run the historical Blender test launcher as the final validated procedure:**
preview suppression, offline mode and later staged validation changes have not
yet been integrated into it. Blender execution/installation requires separate
approval. See the [handoff notes](docs/handoff-2026-11-04.md); older reports and
the [validation plan](docs/validation-plan.md) describe earlier stages.
