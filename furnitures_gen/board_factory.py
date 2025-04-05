import bpy
from mathutils import Vector
# -------------------------------------------------------------------
# UTILITY: Create a "board" (cube scaled to desired X×Y×Z)
# -------------------------------------------------------------------
class BoardFactory:
    @staticmethod
    def add_cladding(wall_name, cladding_type, wall_length, wall_height, thickness, y_offset,
                     material, location, wall, sheet_length, sheet_height):
        # Calculate number of full sheets and if a partial sheet is needed
        num_length_sheets = wall_length // sheet_length
        num_height_sheets = wall_height // sheet_height
        remaining_length = wall_length % sheet_length
        remaining_height = wall_height % sheet_height

        # Wall origin (bottom-left corner)
        start_x = - (wall_length / 2)
        start_z = 0  # Base of the wall

        for col in range(int(num_length_sheets) + (1 if remaining_length > 0 else 0)):
            cladding_length = sheet_length if col < num_length_sheets else remaining_length

            for row in range(int(num_height_sheets) + (1 if remaining_height > 0 else 0)):
                cladding_height = sheet_height if row < num_height_sheets else remaining_height

                if cladding_length <= 0 or cladding_height <= 0:
                    continue  # Skip empty tiles

                # Calculate sheet position
                pos_x = start_x + col * sheet_length + (cladding_length / 2)
                pos_z = start_z + row * sheet_height + (cladding_height / 2)
                world_position = Vector((pos_x, y_offset, pos_z))
                # Create the cladding sheet
                sheet_obj = BoardFactory.add_board(wall,
                                                   board_name=f"{wall_name}_{cladding_type}_{col}_{row}",
                                                   length=cladding_length,
                                                   height=cladding_height,
                                                   depth=thickness,
                                                   location=world_position,
                                                   material=material
                                                   )
                # sheet_obj.parent = wall
                # sheet_obj.location = wall.matrix_world.inverted() @ world_position
                # move_to_collection(sheet_obj, wall_coll)

    @staticmethod
    def add_board(parent=None, board_name=None, length=None, height=None, depth=None, location=None, material=None,
                  bevel_width=0.01, bevel_segments=3,rotation=(0, 0, 0)):
        """
        Create a rectangular 'board' from a unit cube:
          - X-axis = length
          - Y-axis = depth
          - Z-axis = height
        Centered at 'location'.
        """
        bpy.ops.mesh.primitive_cube_add(size=1, location=location)
        obj = bpy.context.object
        obj.name = board_name

        # Correct scaling
        obj.scale = (length, depth, height)  # Ensure full size scaling

        # Apply scale
        bpy.ops.object.transform_apply(scale=True, location=False)
        # **Ensure Origin is at the Actual Center of the Object**
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
        # Add Bevel Modifier for smoother edges
        bevel = obj.modifiers.new(name="Bevel", type='BEVEL')
        bevel.width = bevel_width  # Adjust to control bevel size
        bevel.segments = bevel_segments  # More segments = smoother edges
        bevel.profile = 0.7  # Adjust profile curve

        # Assign material if provided
        if material:
            obj.data.materials.append(material)

        if parent is not None:
            obj.parent = parent
            obj.location = location
            obj.rotation_euler = rotation

        return obj