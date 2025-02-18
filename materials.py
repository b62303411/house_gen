import bpy
# -------------------------------------------------------------------
# MATERIALS (simple placeholders)
# -------------------------------------------------------------------
class MaterialFactory:

    @staticmethod
    def apply_material(obj, material):
        """Applies material to an object if provided."""
        if material:
            if not obj.data.materials:
                obj.data.materials.append(material)
            else:
                obj.data.materials[0] = material
    @staticmethod
    def get_material(name=None):
        # Check if a material with the same or a similar name exists
        existing_materials = bpy.data.materials.keys()
        for mat_name in existing_materials:
            if mat_name.startswith(name):  # Avoids infinite numbered duplicates
                print(f"Material '{mat_name}' already exists. Returning existing material.")
                return bpy.data.materials[mat_name]  # Return the existing material

    @staticmethod
    def get_granite_material():
        granite_material = MaterialFactory.get_material("Granite")
        if granite_material is None:
            """Generates a procedural granite material."""
            granite_material = bpy.data.materials.new(name="Granite")
            granite_material.use_nodes = True
            nodes = granite_material.node_tree.nodes
            nodes.clear()

            output_node = nodes.new(type='ShaderNodeOutputMaterial')
            principled_node = nodes.new(type='ShaderNodeBsdfPrincipled')
            noise_node = nodes.new(type='ShaderNodeTexNoise')
            color_ramp = nodes.new(type='ShaderNodeValToRGB')

            principled_node.location = (-200, 0)
            noise_node.location = (-400, 0)
            color_ramp.location = (-300, 0)

            granite_material.node_tree.links.new(principled_node.outputs['BSDF'], output_node.inputs['Surface'])
            granite_material.node_tree.links.new(noise_node.outputs['Fac'], color_ramp.inputs['Fac'])
            granite_material.node_tree.links.new(color_ramp.outputs['Color'], principled_node.inputs['Base Color'])

            noise_node.inputs['Scale'].default_value = 75.0
            noise_node.inputs['Detail'].default_value = 8.0
            noise_node.inputs['Roughness'].default_value = 0.5

            color_ramp.color_ramp.interpolation = 'B-SPLINE'
            color_ramp.color_ramp.elements[0].position = 0.2
            color_ramp.color_ramp.elements[1].position = 0.8

        return granite_material

    @staticmethod
    def create_acajou_wood_material(name="AcajouWood"):
        """
        Creates a procedural Acajou (mahogany) wood material compatible with Blender 4.0.
        """
        material = MaterialFactory.get_material(name)
        if material is None:
            material = bpy.data.materials.new(name)

        material.use_nodes = True
        nodes = material.node_tree.nodes
        links = material.node_tree.links
        nodes.clear()

        # Create Nodes
        texture_coord = nodes.new(type='ShaderNodeTexCoord')
        mapping = nodes.new(type='ShaderNodeMapping')
        noise = nodes.new(type='ShaderNodeTexNoise')
        color_ramp = nodes.new(type='ShaderNodeValToRGB')
        bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
        output = nodes.new(type='ShaderNodeOutputMaterial')

        # Set Locations
        texture_coord.location = (-600, 0)
        mapping.location = (-400, 0)
        noise.location = (-200, 0)
        color_ramp.location = (0, 0)
        bsdf.location = (200, 0)
        output.location = (400, 0)

        # Link Nodes
        links.new(texture_coord.outputs["Generated"], mapping.inputs["Vector"])
        links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
        links.new(noise.outputs["Fac"], color_ramp.inputs["Fac"])
        links.new(color_ramp.outputs["Color"], bsdf.inputs["Base Color"])
        links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

        # Configure Noise Texture
        noise.inputs["Scale"].default_value = 8.0  # Adjusted for finer detail
        noise.inputs["Detail"].default_value = 5.0
        noise.inputs["Roughness"].default_value = 0.5

        # Configure Color Ramp for Acajou Wood
        color_ramp.color_ramp.elements[0].color = (0.3, 0.15, 0.08, 1)  # Dark brown base
        mid_color = color_ramp.color_ramp.elements.new(0.5)  # Add mid-tone
        mid_color.color = (0.55, 0.3, 0.15, 1)  # Mid brown
        color_ramp.color_ramp.elements[1].color = (0.75, 0.45, 0.2, 1)  # Lightest grain

        # Configure BSDF for Blender 4.0
        bsdf.inputs["Roughness"].default_value = 0.65
        bsdf.inputs["IOR"].default_value = 1.45  # Corrected Blender 4.0 parameter
        #bsdf.inputs["Specular"].default_value = 0.5  # Adjusted for realistic shine

        return material
    @staticmethod
    def create_matrice_material(name="MatriceMaterial"):
        """
        Creates a simple, smooth material for the matrice (bed base).
        """
        material = MaterialFactory.get_material(name)
        if material is None:
            material = bpy.data.materials.new(name)

        material.use_nodes = True
        bsdf = material.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (0.8, 0.8, 0.8, 1.0)  # Light gray
            bsdf.inputs["Roughness"].default_value = 0.3
            bsdf.inputs["IOR"].default_value = 1.45  # Blender 4.0 compatible
            #bsdf.inputs["Specular IOR"].default_value = 1.45  # Updated for Blender 4.0
        return material

    @staticmethod
    def create_drape_material(name="DrapeMaterial"):
        """
        Creates a fabric-like material for the drape.
        """
        material = MaterialFactory.get_material(name)
        if material is None:
            material = bpy.data.materials.new(name)

        material.use_nodes = True
        nodes = material.node_tree.nodes
        links = material.node_tree.links

        # Clear default nodes
        for node in nodes:
            nodes.remove(node)

        # Add nodes
        texture_coord = nodes.new(type='ShaderNodeTexCoord')
        noise = nodes.new(type='ShaderNodeTexNoise')
        color_ramp = nodes.new(type='ShaderNodeValToRGB')
        bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
        output = nodes.new(type='ShaderNodeOutputMaterial')

        # Set node locations
        texture_coord.location = (-400, 0)
        noise.location = (-200, 0)
        color_ramp.location = (0, 0)
        bsdf.location = (200, 0)
        output.location = (400, 0)

        # Link nodes
        links.new(texture_coord.outputs["UV"], noise.inputs["Vector"])
        links.new(noise.outputs["Fac"], color_ramp.inputs["Fac"])
        links.new(color_ramp.outputs["Color"], bsdf.inputs["Base Color"])
        links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

        # Configure noise texture
        noise.inputs["Scale"].default_value = 50.0
        noise.inputs["Detail"].default_value = 2.0
        noise.inputs["Roughness"].default_value = 0.8

        # Configure color ramp for fabric
        color_ramp.color_ramp.elements[0].color = (0.9, 0.8, 0.7, 1)  # Light beige
        color_ramp.color_ramp.elements[1].color = (0.8, 0.7, 0.6, 1)  # Slightly darker beige

        # Configure BSDF for Blender 4.0
        bsdf.inputs["Roughness"].default_value = 0.9
        #bsdf.inputs["Sheen Tint"].default_value = 0.5  # Updated for Blender 4.0
        #bsdf.inputs["Sheen Roughness"].default_value = 0.5  # Updated for Blender 4.0

        return material
    @staticmethod
    def create_wood_material(name="FramingWood"):
        mat = MaterialFactory.get_material(name)
        if mat is None:
            mat = bpy.data.materials.new(name)

        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (0.8, 0.6, 0.4, 1.0)
            bsdf.inputs["Roughness"].default_value = 0.5
        return mat

    @staticmethod
    def create_sheathing_material(name="SheathingOSB"):
        mat = MaterialFactory.get_material(name)
        if mat is None:
            mat = bpy.data.materials.new(name)

        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (0.7, 0.6, 0.4, 1.0)
            bsdf.inputs["Roughness"].default_value = 0.7
        return mat

    @staticmethod
    def create_drywall_material(name="Drywall"):
        mat = MaterialFactory.get_material(name)
        if mat is None:
            mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (0.9, 0.9, 0.9, 1.0)
            bsdf.inputs["Roughness"].default_value = 0.8
        return mat

    @staticmethod
    def create_simple_wood_material(name="Wood"):
        """
        Creates a simple brownish 'wood' material (non-procedural).
        """
        mat = MaterialFactory.get_material(name)
        if mat is None:
            mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs["Base Color"].default_value = (0.6, 0.4, 0.2, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.5
        return mat

    @staticmethod
    def create_procedural_material(name, material_type):
        """
        Creates a procedural material ('wood', 'earth', or 'glass') for demonstration.
        """
        material = MaterialFactory.get_material(name)
        if material is None:
            material = bpy.data.materials.new(name)
        material.use_nodes = True
        nodes = material.node_tree.nodes
        links = material.node_tree.links

        # Clear out the default nodes
        for node in nodes:
            nodes.remove(node)

        # Principled BSDF ShaderNodeBsdfPrincipled
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
            tree = material.node_tree
            material.blend_method = 'BLEND'
            material.shadow_method = 'HASHED'

            # Delete the Principled BSDF
            tree.nodes.remove(bsdf)  # Remove the old node by its reference (bsdf)

            # Create the Glass BSDF
            bsdf = tree.nodes.new('ShaderNodeBsdfGlass')  # Create a new bsdf node
            bsdf.location = (0, 0)

            bsdf.inputs["Color"].default_value = (0.8, 0.9, 1, 0.5)
            bsdf.inputs["IOR"].default_value = 1.45
            bsdf.inputs["Roughness"].default_value = 0.05

            tree.links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])  # Reconnect the output

        return material

    @staticmethod
    def create_materials():
        mat_framing = MaterialFactory.create_wood_material("FramingWood")
        mat_sheathing = MaterialFactory.create_sheathing_material("SheathingOSB")
        mat_drywall = MaterialFactory.create_drywall_material("Drywall")
        mat_glass = MaterialFactory.create_procedural_material("glass", "glass")

        materials = {}
        materials['framing'] = mat_framing
        materials['sheathing'] = mat_sheathing
        materials['drywall'] = mat_drywall
        materials['glass'] = mat_glass
        return materials