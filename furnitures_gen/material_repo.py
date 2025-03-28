import bpy

class MaterialRepo:
    @staticmethod
    def get_or_create_material(material_name):
        material = MaterialRepo.get_material(material_name)
        exist = False
        if material is None:
            material = bpy.data.materials.new(name=material_name)
        else:
            exist = True

        return material,exist

    @staticmethod
    def get_material(name=None):
        # Check if a material with the same or a similar name exists
        existing_materials = bpy.data.materials.keys()
        for mat_name in existing_materials:
            if mat_name.startswith(name):  # Avoids infinite numbered duplicates
                print(f"Material '{mat_name}' already exists. Returning existing material.")
                return bpy.data.materials[mat_name]  # Return the existing material