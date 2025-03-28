import bpy

class FloorFactory:
    def create_tiled_floor(grid_width, grid_depth, room_layout):
        """Creates a tiled floor where each 1x1 ft tile is assigned a room and colored accordingly."""

        # Define room colors
        ROOM_COLORS = {
            "Kitchen": (1.0, 0.7, 0.3, 1),  # Orange
            "Living Room": (0.2, 0.8, 0.3, 1),  # Green
            "Master Bedroom": (0.5, 0.5, 1, 1),  # Blue
            "Child Bedroom": (1.0, 0.4, 0.7, 1),  # Pink
            "Office": (0.7, 0.3, 1, 1),  # Purple
            "Storage": (0.3, 0.3, 0.3, 1),  # Gray
            "Bathroom 1": (0.9, 0.9, 0.9, 1),  # White
            "Bathroom 2": (0.9, 0.9, 0.9, 1),  # White
            "Friends Room": (0.3, 0.8, 0.8, 1),  # Cyan
        }

        tile_objects = []
        meter_to_feet = 0.3048
        for x in range(grid_width):
            for y in range(grid_depth):
                # Determine room assignment
                room_name = room_layout.get((x, y), "Unknown")
                tile_color = ROOM_COLORS.get(room_name, (1, 1, 1, 1))  # Default White

                # Create a floor tile
                bpy.ops.mesh.primitive_plane_add(size=1, location=(x * meter_to_feet, y * meter_to_feet, 0))
                tile = bpy.context.object
                tile.name = f"Tile_{x}_{y}_{room_name}"
                tile.scale = (meter_to_feet, meter_to_feet, 1)  # **Ensure each tile is exactly 1ft x 1ft**
                tile_objects.append(tile)

                # Assign material with color
                mat = bpy.data.materials.new(name=f"Tile_Mat_{room_name}")
                mat.diffuse_color = tile_color
                tile.data.materials.append(mat)
                if x % 3 == 0 and y % 3 == 0:
                    # Add text label for the room name
                    bpy.ops.object.text_add(location=(x * meter_to_feet, y * meter_to_feet, 0.1))
                    text_obj = bpy.context.object
                    text_obj.data.body = room_name
                    text_obj.scale = (meter_to_feet / 4, meter_to_feet / 4, 0.2)
                    text_obj.rotation_euler = (1.57, 0, 0)  # Rotate to face up
                    text_obj.name = f"Label_{room_name}"

        return tile_objects
    @staticmethod
    def color_floor_by_room(room_name, floor_object):
        """ Assigns a unique color to the floor based on room type. """

        # Define room colors
        ROOM_COLORS = {
            "Kitchen": (1.0, 0.7, 0.3, 1),  # Orange
            "Living Room": (0.2, 0.8, 0.3, 1),  # Green
            "Master Bedroom": (0.5, 0.5, 1, 1),  # Blue
            "Child Bedroom": (1.0, 0.4, 0.7, 1),  # Pink
            "Office": (0.7, 0.3, 1, 1),  # Purple
            "Storage": (0.3, 0.3, 0.3, 1),  # Gray
            "Bathroom 1": (0.9, 0.9, 0.9, 1),  # White
            "Bathroom 2": (0.9, 0.9, 0.9, 1),  # White
            "Friends Room": (0.3, 0.8, 0.8, 1),  # Cyan
        }

        # Assign color (default to white if not defined)
        color = ROOM_COLORS.get(room_name, (1, 1, 1, 1))  # Default White

        # Create material
        mat = bpy.data.materials.new(name=f"Room_Mat_{room_name}")
        mat.diffuse_color = color

        # Apply material
        floor_object.data.materials.append(mat)