import bpy

class TexturedPlaneFactory:
    @staticmethod
    def create_textured_plane(image_path, plane_name="TexturedPlane", plane_size=1):
        # Create a new plane
        bpy.ops.mesh.primitive_plane_add(size=plane_size)
        plane = bpy.context.object
        plane.name = plane_name
        # Correct scaling
        plane.scale = (31.8, 15.15, 1)  # Ensure full size scaling

        # Apply scale
        #bpy.ops.object.transform_apply(scale=True, location=False)

        # Create a new material
        mat = bpy.data.materials.new(name="ImageMaterial")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")

        # Remove existing links to prevent issues
        if bsdf:
            mat.node_tree.nodes.remove(bsdf)

        # Add Image Texture Node
        tex_node = mat.node_tree.nodes.new(type="ShaderNodeTexImage")
        tex_node.image = bpy.data.images.load(image_path)

        # Add a New Principled BSDF Node
        bsdf = mat.node_tree.nodes.new(type="ShaderNodeBsdfPrincipled")

        # Add Material Output Node (if not already present)
        output_node = mat.node_tree.nodes.get("Material Output")
        if not output_node:
            output_node = mat.node_tree.nodes.new(type="ShaderNodeOutputMaterial")

        # Connect Nodes
        mat.node_tree.links.new(tex_node.outputs["Color"], bsdf.inputs["Base Color"])
        mat.node_tree.links.new(bsdf.outputs["BSDF"], output_node.inputs["Surface"])

        # Assign material to the plane
        if plane.data.materials:
            plane.data.materials[0] = mat
        else:
            plane.data.materials.append(mat)

        print(f"Created plane '{plane_name}' with texture: {image_path}")
        return plane