# Security and environment

Blender 5.1.1 build b70da489d7f4 was identified by --version in Phase 0.
Git 2.54.0 and system Python 3.14.7 are available. No production scene was read.
Phase 1A adds no external dependency; runtime uses bpy and the standard library.

MCP is prohibited. Static inspection found `uvx mcp-for-blender`, an installed
addon declaring 1.7/protocol 11, a default localhost:9876 endpoint, and an
unrestricted execute_code handler calling exec. Authentication was not apparent
in the inspected receive/dispatch path. Actual running version, endpoint,
telemetry state and Blender compatibility remain unverified. No MCP calls were
made. A loopback endpoint or separate folder does not enforce read-only access.

The proposed CLI wrapper isolates user resource/config/script/extension/data and
temporary paths, disables file auto-execution, and uses factory startup in a new
process. It does not install addons or save user preferences. These measures do
not provide OS-level filesystem or network isolation. For stronger protection,
use a dedicated OS user without access to production files or a VM; such setup
requires separate approval. GPU drivers may still write their own caches.

New results use UUID subdirectories. Test scripts reject existing output paths;
the ZIP builder uses exclusive creation. No Git mutations are authorized.
