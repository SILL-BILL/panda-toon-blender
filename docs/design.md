# Phase 1A design

Implementation is independent of Pencil+ source, assets and UI. No external
assets or packages are used. The product reference is a feature reference only.

## Shader

White Diffuse BSDF -> Shader to RGB -> RGB to BW yields illumination L.
With t1 <= t2, the multiplier is:

`light + (mid-light) * (L<t2) + (dark-mid) * (L<t1)`.

At t1 the middle tone applies; at t2 the light tone applies. Equal thresholds
intentionally collapse the middle zone. Values above 1 select the light zone.
Two Math LESS_THAN nodes, delta/subtract nodes, multiply nodes and add nodes
implement the expression. Base Color multiplied by optional image RGB is then
multiplied by the tone and connected to Emission (strength 1) -> Material Output.
No texture gives a Mix factor of zero, retaining Base Color. No PBR lighting is
applied a second time. No alpha, separate light color or Cycles support is claimed.

Node creation/update lives in nodes/core.py; PropertyGroup and material allocation
in material/; operators and panel in ui/. Each material owns its own graph.
Stable PT_ names are for readability; custom ownership roles and schema version
identify nodes even after renaming. Updates validate types, math modes, links and
active output before changing values. Missing/edited owned graphs cause an error;
there is no automatic deletion or reconstruction. Unrelated nodes remain intact.

## UI

Material Properties offers creation for editable meshes in Object mode. Shared
mesh data is rejected to prevent modifying other objects' slots. New slots are
appended and selected; existing polygon indices remain unchanged. Operator undo
is supported. The engine is not silently changed.

Base Color, existing image selection, thresholds [0,1], and tone multipliers [0,4]
are exposed. Crossing a threshold clamps the edited value to the other threshold;
callbacks have a recursion guard and update existing node inputs. Settings use a
Material PropertyGroup and persist in blend files when the extension is enabled.
Animation of settings is not implemented/validated; callbacks are for UI edits.

## Validation and limitations

Blender 5.1.1 is the validation target; manifest permits 5.1.x and excludes 5.2.
Static tests are not evidence of actual Blender API or EEVEE compatibility.
Shader to RGB captures light color/energy together. White-light tests are required;
shadow edges, sampling, HDR intensity and color management affect appearance.
Realtime viewport behavior, registration, image packing, reload and installed
Extension activation need Blender execution and user visual acceptance.

Future phases: more zones/gradient editing, offsets, vertex colors, normal control,
highlights/reflections, multi-light color controls, outlines, presets/shared settings.
Cycles and complete Unity compatibility are outside Phase 1A.

References consulted in Phase 0:
- https://developer.blender.org/docs/release_notes/5.1/eevee/
- https://docs.blender.org/api/5.1/bpy.types.NodeTreeInterface.html
- Installed Blender 5.1 `scripts/addons_core/bl_pkg/cli/blender_ext.py` manifest validator.
