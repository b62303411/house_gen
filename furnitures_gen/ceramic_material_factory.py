import bpy

from material_repo import MaterialRepo


class CeramicMaterialFactory:
    @staticmethod
    def create_bath_ceramic(material_name="Bath_Ceramic"):

        material, exist = MaterialRepo.get_or_create_material(material_name)

        if exist:
            return material

        material.use_nodes = True

        nodes = material.node_tree.nodes

        # Clear default nodes
        nodes.clear()

        # Add Principled BSDF shader
        principled_bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
        principled_bsdf.location = (0, 0)
        output = nodes.new(type='ShaderNodeOutputMaterial')
        output.location = (400, 0)

        # Link Principled BSDF to Output
        material.node_tree.links.new(principled_bsdf.outputs['BSDF'], output.inputs['Surface'])

        # Add Noise Texture for base color variation
        noise_texture = nodes.new(type='ShaderNodeTexNoise')
        noise_texture.location = (-400, 200)
        noise_texture.inputs['Scale'].default_value = 50.0

        # Add ColorRamp for base color
        color_ramp = nodes.new(type='ShaderNodeValToRGB')
        color_ramp.location = (-200, 200)
        color_ramp.color_ramp.elements[0].color = (0.9, 0.9, 0.9, 1)  # Light gray
        color_ramp.color_ramp.elements[1].color = (0.95, 0.95, 0.95, 1)  # Slightly lighter gray

        # Link Noise Texture to ColorRamp
        material.node_tree.links.new(noise_texture.outputs['Fac'], color_ramp.inputs['Fac'])

        # Link ColorRamp to Principled BSDF Base Color
        material.node_tree.links.new(color_ramp.outputs['Color'], principled_bsdf.inputs['Base Color'])

        # Add Noise Texture for roughness
        noise_roughness = nodes.new(type='ShaderNodeTexNoise')
        noise_roughness.location = (-400, -100)
        noise_roughness.inputs['Scale'].default_value = 100.0

        # Add ColorRamp for roughness
        roughness_ramp = nodes.new(type='ShaderNodeValToRGB')
        roughness_ramp.location = (-200, -100)
        roughness_ramp.color_ramp.elements[0].position = 0.1
        roughness_ramp.color_ramp.elements[1].position = 0.3

        # Link Noise Texture to Roughness ColorRamp
        material.node_tree.links.new(noise_roughness.outputs['Fac'], roughness_ramp.inputs['Fac'])

        # Link Roughness ColorRamp to Principled BSDF Roughness
        material.node_tree.links.new(roughness_ramp.outputs['Color'], principled_bsdf.inputs['Roughness'])

        # Add Bump Map for micro-surface details
        bump = nodes.new(type='ShaderNodeBump')
        bump.location = (-200, -300)
        bump.inputs['Strength'].default_value = 0.1

        # Add Noise Texture for bump
        noise_bump = nodes.new(type='ShaderNodeTexNoise')
        noise_bump.location = (-400, -300)
        noise_bump.inputs['Scale'].default_value = 200.0

        # Link Noise Texture to Bump
        material.node_tree.links.new(noise_bump.outputs['Fac'], bump.inputs['Height'])

        # Link Bump to Principled BSDF Normal
        material.node_tree.links.new(bump.outputs['Normal'], principled_bsdf.inputs['Normal'])
        return material

    @staticmethod
    def create_procedural_ceramic_material2(material_name="ProceduralCeramic"):
        material, exist = MaterialRepo.get_or_create_material(material_name)
        if exist:
            return material
        """Creates a procedural ceramic material with gloss, roughness variation, and optional grout lines."""

        # Create a new material
        material.use_nodes = True
        nodes = material.node_tree.nodes
        links = material.node_tree.links

        # Clear default nodes
        for node in nodes:
            nodes.remove(node)

        # **Principled BSDF Shader**
        principled_bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
        principled_bsdf.location = (0, 0)

        # **Noise Texture (Imperfections)**
        noise_texture = nodes.new(type='ShaderNodeTexNoise')
        noise_texture.location = (-300, 200)
        noise_texture.inputs["Scale"].default_value = 100
        noise_texture.inputs["Detail"].default_value = 5
        noise_texture.inputs["Roughness"].default_value = 0.5

        # **Color Ramp (Smooth Imperfections)**
        color_ramp = nodes.new(type='ShaderNodeValToRGB')
        color_ramp.location = (-100, 200)
        color_ramp.color_ramp.interpolation = 'EASE'
        color_ramp.color_ramp.elements[0].position = 0.3
        color_ramp.color_ramp.elements[1].position = 0.7

        # **Tile Pattern (Using Voronoi Texture)**
        voronoi_texture = nodes.new(type='ShaderNodeTexVoronoi')
        voronoi_texture.location = (-300, -100)
        voronoi_texture.inputs["Scale"].default_value = 8  # Adjust for tile size
        voronoi_texture.feature = 'F1'

        # **Bump Node (For Subtle Surface Details)**
        bump_node = nodes.new(type='ShaderNodeBump')
        bump_node.location = (-100, 0)
        bump_node.inputs["Strength"].default_value = 0.1

        # **Mix Shader (To Add Grout Between Tiles)**
        mix_shader = nodes.new(type='ShaderNodeMixShader')
        mix_shader.location = (300, 0)

        # **Grout Color**
        grout_color = nodes.new(type='ShaderNodeRGB')
        grout_color.location = (-100, -200)
        grout_color.outputs["Color"].default_value = (0.2, 0.2, 0.2, 1)  # Dark grout

        # **Material Output**
        material_output = nodes.new(type='ShaderNodeOutputMaterial')
        material_output.location = (500, 0)

        # **Link Nodes**
        links.new(noise_texture.outputs["Fac"], color_ramp.inputs["Fac"])
        links.new(color_ramp.outputs["Color"], bump_node.inputs["Height"])
        links.new(bump_node.outputs["Normal"], principled_bsdf.inputs["Normal"])

        # Use Voronoi texture to create grout lines
        links.new(voronoi_texture.outputs["Distance"], mix_shader.inputs["Fac"])
        links.new(grout_color.outputs["Color"], mix_shader.inputs[1])
        links.new(principled_bsdf.outputs["BSDF"], mix_shader.inputs[2])

        # Output final material
        links.new(mix_shader.outputs["Shader"], material_output.inputs["Surface"])

        # Assign material to active object
        if bpy.context.object:
            if bpy.context.object.type == 'MESH':
                if not bpy.context.object.data.materials:
                    bpy.context.object.data.materials.append(material)
                else:
                    bpy.context.object.data.materials[0] = material

        return material