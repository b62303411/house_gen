import bpy
from mathutils import Vector
from furniture_factory import FurnitureFactory
from materials import MaterialFactory


class BedFactory:
    @staticmethod
    def create_bed(name="Bed", length=2.03, width=1.93, height=0.5, materials=None, location=(0, 0, 0)):
        """Creates a simple bed frame with a headboard using a parent-child hierarchy."""
        #matrice_mat = materials["matrice"]
        #board_mat = materials["board"]
        #drape_mat = materials["drape"]
        # Create materials
        board_mat = MaterialFactory.create_acajou_wood_material()
        matrice_mat = MaterialFactory.create_matrice_material()
        drape_mat = MaterialFactory.create_drape_material()

        # Create an empty object as the parent
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=location)
        bed_parent = bpy.context.object
        bed_parent.name = name
        #, location = (location[0], location[1], location[2] + height / 2)
        # Mattress
        bpy.ops.mesh.primitive_cube_add(size=1)
        mattress = bpy.context.object
        mattress.name = f"{name}_Mattress"
        mattress.scale = (length, width, height/2)
        mattress.parent = bed_parent
        bpy.ops.object.transform_apply(scale=True)
        mattress.location = (0, 0, height/4+0.1)

        if matrice_mat:
            FurnitureFactory.apply_material(mattress, matrice_mat)

        # Headboard
        bpy.ops.mesh.primitive_cube_add(size=1)
        headboard = bpy.context.object
        headboard.name = f"{name}_Headboard"
        headboard.scale = (0.05, width, height)
        headboard.parent = bed_parent
        bpy.ops.object.transform_apply(scale=True)
        headboard.location = (length/2, 0, height/2)
        if board_mat:
            FurnitureFactory.apply_material(headboard, board_mat)

        board_thickness= 0.1
        # Board (Bed Frame)
        bpy.ops.mesh.primitive_cube_add(size=1)
        board = bpy.context.object
        board.name = f"{name}_Board"
        board.scale = (length + board_thickness, width +board_thickness, board_thickness)
        board.parent = bed_parent
        bpy.ops.object.transform_apply(scale=True)
        board.location = (0, 0, board_thickness / 2)

        if drape_mat:
            FurnitureFactory.apply_material(board, board_mat)
            # Drape (Cloth with Physics)
            bpy.ops.mesh.primitive_plane_add(size=1)
            drape = bpy.context.object
            drape.name = f"{name}_Drape"
            drape.scale = (length+.2, width+.2, 1)
            drape.parent = bed_parent
            bpy.ops.object.transform_apply(scale=True)
            drape.location = (0, 0, height / 2 + 0.1)
            drape.data.materials.append(drape_mat)

            # Enable Cloth Physics for the Drape
            bpy.context.view_layer.objects.active = drape
            bpy.ops.object.modifier_add(type='CLOTH')
            cloth_modifier = drape.modifiers["Cloth"]
            cloth_modifier.settings.quality = 5
            cloth_modifier.settings.tension_stiffness = 15
            cloth_modifier.settings.compression_stiffness = 15
            cloth_modifier.settings.bending_stiffness = 10
            cloth_modifier.settings.use_pressure = True
            cloth_modifier.settings.uniform_pressure_force = 2.0
        return bed_parent