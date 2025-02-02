bl_info = {
    "name": "House Generator",
    "author": "Your Name",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Tool Shelf",
    "description": "Procedurally generate passive house models",
    "category": "Object",
}

import bpy
import sys
import os

# Path to the modules
addon_dir = os.path.dirname(__file__)
module_path = os.path.join(addon_dir, "HouseGenerator")
if module_path not in sys.path:
    sys.path.append(module_path)

from HouseGenerator import foundation, walls, roof, windows, exporter

class OBJECT_OT_generate_house(bpy.types.Operator):
    bl_idname = "object.generate_house"
    bl_label = "Generate House"
    bl_description = "Generates a passive house model"

    def execute(self, context):
        # Example usage of your modules
        foundation.create_foundation()
        walls.create_walls()
        roof.create_roof()
        windows.create_windows()
        exporter.export_to_fbx()  # or your preferred format
        return {'FINISHED'}

def menu_func(self, context):
    self.layout.operator(OBJECT_OT_generate_house.bl_idname)

def register():
    bpy.utils.register_class(OBJECT_OT_generate_house)
    bpy.types.VIEW3D_MT_mesh_add.append(menu_func)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_generate_house)
    bpy.types.VIEW3D_MT_mesh_add.remove(menu_func)

if __name__ == "__main__":
    register()
