# materials.py
import bpy
# -------------------------------------------------------------------
# MATERIALS (simple placeholders)
# -------------------------------------------------------------------

def create_wood_material(name="FramingWood"):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.8, 0.6, 0.4, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.5
    return mat

def create_sheathing_material(name="SheathingOSB"):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.7, 0.6, 0.4, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.7
    return mat

def create_drywall_material(name="Drywall"):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.9, 0.9, 0.9, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.8
    return mat
def create_simple_wood_material(name="Wood"):
    """
    Creates a simple brownish 'wood' material (non-procedural).
    """
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (0.6, 0.4, 0.2, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.5
    return mat

def create_procedural_material(name, material_type):
    """
    Creates a procedural material ('wood', 'earth', or 'glass') for demonstration.
    """
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links

    # Clear out the default nodes
    for node in nodes:
        nodes.remove(node)

    # Principled BSDF
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    # Material Output
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (200, 0)
    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

    # Choose material type
    if material_type == "wood":
        noise = nodes.new(type='ShaderNodeTexNoise')
        noise.inputs["Scale"].default_value = 10.0
        color_ramp = nodes.new(type='ShaderNodeValToRGB')
        color_ramp.color_ramp.elements[0].color = (0.6, 0.4, 0.2, 1)
        color_ramp.color_ramp.elements[1].color = (0.8, 0.6, 0.4, 1)
        links.new(noise.outputs["Fac"], color_ramp.inputs["Fac"])
        links.new(color_ramp.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = 0.7

    elif material_type == "earth":
        noise = nodes.new(type='ShaderNodeTexNoise')
        noise.inputs["Scale"].default_value = 20.0
        color_ramp = nodes.new(type='ShaderNodeValToRGB')
        color_ramp.color_ramp.elements[0].color = (0.4, 0.3, 0.2, 1)
        color_ramp.color_ramp.elements[1].color = (0.6, 0.5, 0.4, 1)
        links.new(noise.outputs["Fac"], color_ramp.inputs["Fac"])
        links.new(color_ramp.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = 0.9

    elif material_type == "glass":
        bsdf.inputs["Base Color"].default_value = (0.8, 0.9, 1, 0.5)
        bsdf.inputs["Transmission"].default_value = 1.0
        bsdf.inputs["Roughness"].default_value = 0.1
        bsdf.inputs["IOR"].default_value = 1.45

    return material
