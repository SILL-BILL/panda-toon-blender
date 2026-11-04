# SPDX-License-Identifier: GPL-3.0-or-later
"""Owned, per-material shader graph. Updates never rebuild a graph."""
OWNER = "panda_toon_owner"
SCHEMA = "panda_toon_schema"
VERSION = 1
TYPES = {
    "diffuse": "ShaderNodeBsdfDiffuse", "rgb": "ShaderNodeShaderToRGB",
    "luma": "ShaderNodeRGBToBW", "low": "ShaderNodeMath",
    "high": "ShaderNodeMath", "dark": "ShaderNodeValue",
    "mid": "ShaderNodeValue", "light": "ShaderNodeValue",
    "mid_delta": "ShaderNodeMath", "light_delta": "ShaderNodeMath",
    "mid_step": "ShaderNodeMath", "light_step": "ShaderNodeMath",
    "sum_mid": "ShaderNodeMath", "tone": "ShaderNodeMath",
    "base": "ShaderNodeRGB", "texture": "ShaderNodeTexImage",
    "tint": "ShaderNodeMixRGB", "shade": "ShaderNodeMixRGB",
    "emission": "ShaderNodeEmission", "output": "ShaderNodeOutputMaterial",
}
EDGES = [
    ("diffuse", 0, "rgb", 0), ("rgb", 0, "luma", 0),
    ("luma", 0, "low", 0), ("luma", 0, "high", 0),
    ("mid", 0, "mid_delta", 0), ("light", 0, "mid_delta", 1),
    ("dark", 0, "light_delta", 0), ("mid", 0, "light_delta", 1),
    ("high", 0, "mid_step", 0), ("mid_delta", 0, "mid_step", 1),
    ("low", 0, "light_step", 0), ("light_delta", 0, "light_step", 1),
    ("light", 0, "sum_mid", 0), ("mid_step", 0, "sum_mid", 1),
    ("sum_mid", 0, "tone", 0), ("light_step", 0, "tone", 1),
    ("base", 0, "tint", 1), ("texture", 0, "tint", 2),
    ("tint", 0, "shade", 1), ("tone", 0, "shade", 2),
    ("shade", 0, "emission", 0), ("emission", 0, "output", 0),
]
OPERATIONS = {"low": "LESS_THAN", "high": "LESS_THAN",
              "mid_delta": "SUBTRACT", "light_delta": "SUBTRACT",
              "mid_step": "MULTIPLY", "light_step": "MULTIPLY",
              "sum_mid": "ADD", "tone": "ADD"}


def inspect(material):
    if material.get(SCHEMA) != VERSION or material.node_tree is None:
        raise ValueError("Not a supported Panda Toon material")
    nodes = {}
    for node in material.node_tree.nodes:
        role = node.get(OWNER)
        if role in TYPES:
            if role in nodes or node.bl_idname != TYPES[role]:
                raise ValueError("Panda Toon graph ownership/type conflict")
            nodes[role] = node
    if set(nodes) != set(TYPES):
        raise ValueError("Panda Toon nodes are missing; create a new material")
    for role, operation in OPERATIONS.items():
        if nodes[role].operation != operation or nodes[role].use_clamp:
            raise ValueError("Panda Toon math operation was edited")
    for role in ("tint", "shade"):
        if nodes[role].blend_type != "MULTIPLY" or nodes[role].use_clamp:
            raise ValueError("Panda Toon color operation was edited")
    expected = {(nodes[a].outputs[b], nodes[c].inputs[d]) for a,b,c,d in EDGES}
    actual = {(link.from_socket, link.to_socket) for link in material.node_tree.links
              if link.to_node in nodes.values()}
    if actual != expected or not nodes["output"].is_active_output:
        raise ValueError("Panda Toon connections/output were edited")
    return nodes


def _standard_nodes(material):
    """Validate the complete default graph before removing any node."""
    tree = material.node_tree
    if (tree is None or SCHEMA in material or material.users != 0
            or material.animation_data is not None or tree.animation_data is not None):
        raise ValueError("Unexpected new material state")
    defaults = tuple(tree.nodes)
    if (len(defaults) != 2 or {n.bl_idname for n in defaults} !=
            {"ShaderNodeBsdfPrincipled", "ShaderNodeOutputMaterial"}):
        raise ValueError("Unexpected standard material nodes")
    bsdf = next(n for n in defaults if n.bl_idname == "ShaderNodeBsdfPrincipled")
    output = next(n for n in defaults if n.bl_idname == "ShaderNodeOutputMaterial")
    if (any(n.mute or len(n.keys()) for n in defaults)
            or not output.is_active_output or output.target != "ALL"):
        raise ValueError("Edited standard material nodes")
    links = tuple(tree.links)
    if (len(links) != 1 or links[0].from_socket != bsdf.outputs[0]
            or links[0].to_socket != output.inputs[0]):
        raise ValueError("Unexpected standard material connections")
    return defaults


def build_new(material):
    from ..material.service import _claim_new_material
    _claim_new_material(material)
    defaults = _standard_nodes(material)
    # Only this call's newly allocated material and verified defaults are touched.
    for node in defaults:
        material.node_tree.nodes.remove(node)
    nodes = {}
    for index, (role, kind) in enumerate(TYPES.items()):
        node = material.node_tree.nodes.new(kind)
        node[OWNER] = role
        node.name = "PT_" + role
        node.label = "Panda Toon: " + role
        node.location = ((index // 4) * 220, -(index % 4) * 190)
        nodes[role] = node
    for role, operation in OPERATIONS.items():
        nodes[role].operation = operation
        nodes[role].use_clamp = False
    for role in ("tint", "shade"):
        nodes[role].blend_type = "MULTIPLY"
        nodes[role].use_clamp = False
    for a,b,c,d in EDGES:
        material.node_tree.links.new(nodes[a].outputs[b], nodes[c].inputs[d])
    material[SCHEMA] = VERSION
    update(material)


def update(material):
    nodes = inspect(material)
    p = material.panda_toon
    # Less-than masks: light + (mid-light)*[L<high] + (dark-mid)*[L<low].
    nodes["low"].inputs[1].default_value = p.threshold_low
    nodes["high"].inputs[1].default_value = p.threshold_high
    nodes["dark"].outputs[0].default_value = p.dark_tone
    nodes["mid"].outputs[0].default_value = p.mid_tone
    nodes["light"].outputs[0].default_value = p.light_tone
    nodes["base"].outputs[0].default_value = p.base_color
    nodes["texture"].image = p.texture
    nodes["tint"].inputs[0].default_value = 1.0 if p.texture else 0.0
    nodes["shade"].inputs[0].default_value = 1.0
    nodes["diffuse"].inputs[0].default_value = (1, 1, 1, 1)
    nodes["diffuse"].inputs[1].default_value = 0.0
    nodes["emission"].inputs[1].default_value = 1.0
    material.diffuse_color = p.base_color
