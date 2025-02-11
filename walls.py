import bpy
import math
import os
import sys
from mathutils import Vector
from math import radians
from mathutils import Euler
# Add current directory to Python path

def get_script_dir():
    """Get the directory of the current script, handling different contexts."""
    try:
        # First try to get path from text editor
        script_dir = os.path.dirname(bpy.context.space_data.text.filepath)
    except (AttributeError, TypeError):
        try:
            # Fall back to the __file__ attribute
            script_dir = os.path.dirname(os.path.abspath(__file__))
        except NameError:
            # If all else fails, use the Blender executable directory
            script_dir = os.path.dirname(bpy.app.binary_path)
    
    return script_dir
script_dir = get_script_dir()
if script_dir not in sys.path:
    sys.path.append(script_dir)
    
import importlib
import materials
import board_factory
import windows
import segment_factory
import house_factory
importlib.reload(materials)  # Force refresh
importlib.reload(board_factory)
importlib.reload(windows)
importlib.reload(segment_factory)
importlib.reload(house_factory)

from materials import MaterialFactory
from board_factory import BoardFactory
from windows import WindowFactory

from house_factory import HouseFactory
# -------------------------------------------------------------------
# CONSTANTS/DEFAULTS
# -------------------------------------------------------------------

# Typical 2×4 approximation in meters:
STUD_THICKNESS = 0.0381  # 1.5 inches
STUD_WIDTH = 0.0889  # 3.5 inches
STUD_SPACING = 0.4064  # ~16 inches on center

# Constants for Wall Thickness
EXTERIOR_WALL_THICKNESS = 0.4  # 40cm (Earthship-style walls)
INTERIOR_WALL_THICKNESS = 0.15  # 15cm (Wood framing)


# -------------------------------------------------------------------
# UTILITY: Move object to a specific collection
# -------------------------------------------------------------------
@staticmethod
def move_to_collection(obj, target_coll):
    """Unlink 'obj' from all collections, then link to 'target_coll'."""
    if not obj or not target_coll:
        return
    for c in obj.users_collection:
        c.objects.unlink(obj)
    target_coll.objects.link(obj)


# -------------------------------------------------------------------
# CREATE FRAMED WALL with Sheathing (exterior) & Drywall (interior)
# -------------------------------------------------------------------
class WallFactory:
    STUD_SPECS = {
        "2x4": {"thickness": 0.0381, "width": 0.0889},  # 1.5" x 3.5"
        "2x6": {"thickness": 0.0381, "width": 0.1397},  # 1.5" x 5.5"
        "2x8": {"thickness": 0.0381, "width": 0.1905},  # 1.5" x 7.5"
        "2x12": {"thickness": 0.0381, "width": 0.2921}  # 1.5" x 11.5"
    }

    @staticmethod
    def create_wall(name, length, height, location, thickness, rotation, materials, window_specs=None, stud_spec="2x4"):
        """
        Creates a framed wall and applies the correct rotation.
        """
        print(f"create wall 🔎 , at 🔎: {name, str(location)}")

        window_spec = None
        if window_specs is not None:
            window_spec = window_specs[0]

        # Convert thickness to a list of tuples (name, thickness)
        stud_options = [(name, spec["width"]) for name, spec in WallFactory.STUD_SPECS.items()]

        # Find the closest match
        best_match = min(stud_options, key=lambda x: abs(x[1] - thickness))

        stud_spec = best_match[0]

        wall = WallFactory.create_framed_wall(
            name=name,
            length=length,
            height=height,
            location=location,
            stud_spacing=STUD_SPACING,
            stud_spec=stud_spec,
            window_specs=window_specs,
            materials=materials
        )

        # Rotate Wall Based on Orientation
        wall.rotation_euler = rotation

        return wall

   

    @staticmethod
    def create_framed_wall(
            name,
            length,
            height,  # total wall height, including bottom + top plates
            location=(0, 0, 0),
            stud_spacing=STUD_SPACING,
            stud_width=STUD_WIDTH,
            bottom_plate_count=1,
            top_plate_count=2,
            add_sheathing=True,
            add_drywall=True,
            window_specs=None,
            materials=None,
            stud_spec="2x4",
    ):
        material_framing = materials['framing']
        material_sheathing = materials['sheathing']
        material_drywall = materials['drywall']
        material_glass = materials['glass']
        """
        Creates a rectangular framed wall:
          - bottom_plate_count (1 typical),
          - top_plate_count (2 typical, for double top plates),
          - vertical studs spaced on 'stud_spacing',
          - optional single window opening,
          - optional exterior sheathing (one big panel),
          - optional interior drywall (one big panel).

        Returns a Collection containing all parts of this wall.
        """
        stud_thickness = WallFactory.STUD_SPECS[stud_spec]["thickness"]  # Always 1.5"
        stud_width = WallFactory.STUD_SPECS[stud_spec]["width"]  # 3.5", 5.5", etc.

        # **STEP 1: Create the Parent Wall Object**
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=location)
        wall_parent = bpy.context.object
        wall_parent.name = name

        """
        Ensures the wall's origin is at its correct center.
        """
        bpy.ops.object.select_all(action='DESELECT')
        wall_parent.select_set(True)
        bpy.context.view_layer.objects.active = wall_parent

        # Set origin to the bottom center
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')

        # Apply all transforms (scale, rotation, location)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

        # 1) BOTTOM PLATES
        plate_thickness = stud_thickness
        plate_depth = stud_width
        # wall_parent.matrix_world.inverted() @ plate_world_position
        total_bottom_height = plate_thickness * bottom_plate_count
        for i in range(bottom_plate_count):
            z_plate = plate_thickness / 2.0 + i * plate_thickness
            plate_position = Vector((0, 0, z_plate))
            # WallFactory.create_child(wall_parent,f"{name}_BottomPlate_{i + 1}",length,0)
            plate = BoardFactory.add_board(wall_parent,
                                           board_name=f"{name}_BottomPlate_{i + 1}",
                                           length=length,
                                           height=plate_thickness,
                                           depth=plate_depth,
                                           location=plate_position,
                                           material=material_framing
                                           )
            # plate.parent = wall_parent
            # plate.location = wall_parent.matrix_world.inverted() @ plate_world_position
            # move_to_collection(plate, wall_coll)

        # 2) TOP PLATES
        total_top_height = plate_thickness * top_plate_count
        z_top_start = height - total_top_height
        for i in range(top_plate_count):
            z_plate = z_top_start + plate_thickness / 2.0 + i * plate_thickness
            plate_position = Vector((0, 0, z_plate))
            plate = BoardFactory.add_board(wall_parent,
                                           board_name=f"{name}_TopPlate_{i + 1}",
                                           length=length,
                                           height=plate_thickness,
                                           depth=stud_width,
                                           location=plate_position,
                                           material=material_framing
                                           )
            # plate.parent = wall_parent  # Parent to the main wall object
            # plate.location = wall_parent.matrix_world.inverted() @ plate_world_position

        # 3) STUD REGION
        # The "net" region for studs is from top of bottom plates to bottom of top plates.
        stud_region_height = height - (total_bottom_height + total_top_height)
        if stud_region_height < 0:
            stud_region_height = 0
        z_stud_bottom = total_bottom_height

        # Place studs along X at 'stud_spacing' intervals
        x_left = - (length / 2.0) + (stud_thickness / 2.0)
        n_studs = int((length - stud_width) // stud_spacing) + 1

        for i in range(n_studs):
            x_i = x_left + i * stud_spacing
            if x_i + stud_width / 2.0 > (length / 2.0):
                break
            z_center = z_stud_bottom + stud_region_height / 2.0
            stud_position = Vector((x_i, 0, z_center))
            stud_obj = BoardFactory.add_board(wall_parent,
                                              board_name=f"{name}_Stud_{i + 1}",
                                              length=stud_thickness,
                                              height=stud_region_height,
                                              depth=stud_width,
                                              location=stud_position,
                                              material=material_framing
                                              )
            # move_to_collection(stud_obj, wall_coll)
            # stud_obj.parent = wall_parent
            # stud_obj.location = wall_parent.matrix_world.inverted() @  stud_world_position

        # 5) Exterior Sheathing
        if add_sheathing:
            sheathing_thickness = 0.012  # ~12 mm
            # Sheathing goes on the "outside" (we'll treat negative Y as outside)
            sheathing_y = - (plate_depth / 2.0 + sheathing_thickness / 2.0)

            BoardFactory.add_cladding(
                wall_name=name,
                cladding_type="Sheathing",
                wall_length=length,
                wall_height=height,
                thickness=sheathing_thickness,
                y_offset=sheathing_y,
                material=material_sheathing,
                location=location,
                wall=wall_parent,
                sheet_length=2.44,  # Standard 8ft sheet
                sheet_height=1.22  # Standard 4ft sheet
            )

            sheathing_z = height / 2.0

        # 6) Interior Drywall
        if add_drywall:
            drywall_thickness = 0.0127  # 1/2 inch ~ 0.0127 m
            # We'll treat +Y as inside, so place drywall behind studs
            drywall_y = (plate_depth / 2.0 + drywall_thickness / 2.0)
            drywall_z = height / 2.0
            drywall_obj = BoardFactory.add_board(wall_parent,
                                                 board_name=f"{name}_Drywall",
                                                 length=length,
                                                 height=height,
                                                 depth=drywall_thickness,
                                                 location=(0, drywall_y, drywall_z),
                                                 material=material_drywall
                                                 )
            # move_to_collection(drywall_obj, wall_coll)
            drywall_obj.parent = wall_parent
            
        # 4) WINDOW FRAMING (optional)
        if window_specs:
            for ws in window_specs:
                WindowFactory.create_window_opening(
                    wall=wall_parent,
                    name_prefix=f"{name}_Window",
                    window_center_x=ws["center_x"],
                    window_bottom_z=ws["bottom_z"],
                    window_width=ws["width"],
                    window_height=ws["height"],
                    bottom_plate_height=total_bottom_height,
                    top_plate_height=plate_thickness,
                    stud_spec=spec,
                    wall_height=height,
                    second_top_plate_height=plate_thickness if top_plate_count > 1 else 0,
                    material=material_framing,
                    glass_material=material_glass
                )
        return wall_parent

# House Layout Grid (Rows & Columns)
HOUSE_LAYOUT = [
    ["living_room", "friends_family_room"],
    ["kitchen", "bathroom1", "bathroom2"],
    ["child_bedroom", "master_bedroom"],
    ["office", "storage"]
]
# Define Room Dimensions (Width, Length)
ROOM_DIMENSIONS = {
    "kitchen": (4, 3),
    "bathroom1": (2.5, 2),
    "bathroom2": (2.5, 2),
    "child_bedroom": (4, 3),
    "master_bedroom": (5, 4),
    "office": (3.5, 3),
    "storage": (3, 2.5),
    "living_room": (5, 4),
    "friends_family_room": (5, 3.5)
}


# -------------------------------------------------------------------
# TEST / DEMO
# -------------------------------------------------------------------
@staticmethod
def demo_wall_test():
    """
    Demonstrates creating one wall with:
      - Correct stud length
      - Sheathing
      - Drywall
      - An optional window
    Then places a camera & sun so you can see it.
    """
    materials = MaterialFactory.create_materials()
    # Clear scene
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    # We'll create a 4m wide, 3m tall wall (from bottom plate to top plate)
    wall_length = 4.0
    wall_height = 3.0

    # Example window specs
    window_info = {
        "center_x": 0.0,
        "bottom_z": 1.0,
        "width": 1.0,
        "height": 1.2
    }
    window_specs = []
    window_specs.append(window_info)
    # rotation =math.radians(180 / math.pi)
    WallFactory.create_wall(
        name="SouthWall",
        length=wall_length,
        height=wall_height,
        location=(5, -10, 0),
        thickness=EXTERIOR_WALL_THICKNESS,
        rotation=(0, 0, math.radians(90)),  # No Rotation
        materials=HouseFactory.materials,
        window_specs=window_specs  # Add Windows
    )
    # Create the framed wall
    wall_coll = WallFactory.create_framed_wall(
        name="TestWall",
        length=wall_length,
        height=wall_height,
        location=(0, 0, 0),
        stud_spacing=STUD_SPACING,
        bottom_plate_count=1,
        top_plate_count=2,
        add_sheathing=True,
        add_drywall=True,
        window_specs=window_info,  # comment out to remove window
        materials=materials)

    # Camera
    bpy.ops.object.camera_add(location=(5, -5, 2.5))
    cam = bpy.context.object
    cam.rotation_euler = (math.radians(60), 0, math.radians(45))
    bpy.context.scene.camera = cam

    # Sun
    bpy.ops.object.light_add(type='SUN', location=(4, -4, 5))
    sun = bpy.context.object
    sun.rotation_euler = (math.radians(60), 0, math.radians(45))

    # Render settings
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.samples = 64
    bpy.context.scene.render.resolution_x = 1280
    bpy.context.scene.render.resolution_y = 720


def define_room_layout(grid_width, grid_depth):
    """Defines which room each grid cell belongs to."""

    layout = {}

    for x in range(grid_width):
        for y in range(grid_depth):
            if x < 10 and y < 10:
                layout[(x, y)] = "Kitchen"
            elif x >= 10 and x < 20 and y < 10:
                layout[(x, y)] = "Living Room"
            elif x >= 20 and y < 10:
                layout[(x, y)] = "Master Bedroom"
            elif x < 10 and y >= 10 and y < 20:
                layout[(x, y)] = "Office"
            elif x >= 10 and x < 20 and y >= 10 and y < 20:
                layout[(x, y)] = "Storage"
            elif x >= 20 and y >= 10 and y < 20:
                layout[(x, y)] = "Child Bedroom"
            elif x < 10 and y >= 20:
                layout[(x, y)] = "Bathroom 1"
            elif x >= 20 and y >= 20:
                layout[(x, y)] = "Bathroom 2"
            else:
                layout[(x, y)] = "Friends Room"

    return layout


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




def build_entire_perimeter_example():
    # Example footprint: a rectangular building
    footprint_points = [
        (0, 0),
        (15, 0),
        (15, 10),
        (0, 10)
    ]

    # Materials
    mats = MaterialFactory.create_materials()
    ws =  [
        {"center_x": -5 , "bottom_z": 0.5, "width": 1.5, "height": 2},
        {"center_x": 0 , "bottom_z": 0.5, "width": 1.5, "height": 2},
        {"center_x": 5 , "bottom_z": 0.5, "width": 1.5, "height": 2}
    ]
    windows_spec = []
    windows_spec.append(ws)
    windows_spec.append(ws)
    windows_spec.append(ws)
    windows_spec.append(ws)

    # Create the outer wall with segments & corners
    wall_parent = HouseFactory.create_outer_wall(
        name="OuterWall",
        footprint_points=footprint_points,
        wall_height=3.0,
        stud_spacing=0.4064,
        materials=mats,
        windows_spec=windows_spec
    )

    print("✅ Finished building single multi-segment outer wall with corners.")

if __name__ == "__main__":
    # demo_wall_test()
    build_entire_perimeter_example()
    # Camera
    bpy.ops.object.camera_add(location=(5, -5, 2.5))
    cam = bpy.context.object
    cam.rotation_euler = (math.radians(60), 0, math.radians(45))
    bpy.context.scene.camera = cam

    # Sun
    bpy.ops.object.light_add(type='SUN', location=(4, -4, 5))
    sun = bpy.context.object
    sun.rotation_euler = (math.radians(60), 0, math.radians(45))

    # Render settings
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.samples = 64
    bpy.context.scene.render.resolution_x = 1280
    bpy.context.scene.render.resolution_y = 720