# Panda Toon development rules

- Work within this repository. Read existing files, Git status and instructions before editing.
- Preserve user data and unrelated edits. Never open production Blender files. Never delete or replace nodes not owned by Panda Toon.
- Blender MCP is prohibited, including read tools, telemetry changes and arbitrary Python execution.
- Blender CLI tests require explicit approval of the command, scripts, inputs, outputs, locations and risks before execution. Use factory startup, disabled auto-execution, isolated configuration and new output names.
- No dependency, MCP or Extension installation/update or environment change without approval. Audit source, version, license and security before introducing dependencies; prefer Blender and Python standard libraries.
- Commit, push and other Git mutations require approval. Read-only Git inspection is permitted.
- Existing file changes must remain within approved scope; present proposed changes before additional out-of-scope edits. Never overwrite existing generated outputs.
- License is GPL-3.0-or-later by explicit project-owner approval. Any future license change needs approval.
- Rendering tests do not replace the user's visual acceptance. Report facts, assumptions and untested behavior separately.
- Authorization is task-scoped: earlier isolated Blender tests required separate approvals; these do not authorize arbitrary reruns on a new machine.
- One-time authorization (2026-11-04): create `wip/phase1a-2026-11-04`, commit the reviewed WIP sources/docs/tests and push that branch to the existing origin. Exclude lab artifacts, logs, caches, ZIPs and secrets. No main merge or Release. This does not grant blanket approval for later commits/pushes or Blender execution.
