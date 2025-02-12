import bpy
import math
import os
import sys
from mathutils import Vector


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

importlib.reload(materials)  # Force refresh
importlib.reload(board_factory)
importlib.reload(windows)
importlib.reload(segment_factory)


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