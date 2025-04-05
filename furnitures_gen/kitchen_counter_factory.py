import os
import sys


def get_script_dir():
    """Get only the directory of the current script without the file name."""
    script_dir = None

    try:
        # Try getting the directory from Blender text editor
        script_path = bpy.context.space_data.text.filepath
        if script_path:
            script_dir = os.path.dirname(os.path.abspath(script_path))  # Ensure only the folder
    except (AttributeError, TypeError):
        pass

    if not script_dir:
        try:
            # Fall back to __file__ attribute
            script_path = os.path.abspath(__file__)
            script_dir = os.path.dirname(script_path)  # Extract only the directory
        except NameError:
            # If all else fails, use Blender's executable directory
            script_dir = os.path.dirname(bpy.app.binary_path)

    return script_dir

script_dir = get_script_dir()
if script_dir not in sys.path:
    sys.path.append(script_dir)
    sys.path.append("E:\workspace\blender_house\house_gen")

print("Updated script_dir:", script_dir)
# Debugging: Print sys.path to check if it's added
#print("Updated sys.path:", sys.path)



print("Python Executable:", sys.executable)
print("Python Version:", sys.version)
print("Current Working Directory:", os.getcwd())
#print("Sys Path:", sys.path)
import os

script_dir = "/"
print("Files in script directory:", os.listdir(script_dir))

import importlib

import bpy

import math

from mathutils import Vector

from furnitures_gen import basin_factory
from furnitures_gen.basin_factory import BassinFactory

importlib.reload(basin_factory)

class KitchenCounterFactory:
    @staticmethod
    def create_post(parent_obj, location, name_prefix, scale, frame_objects, cabinet_height):
        x = float(location[0])
        y = float(location[1])
        z = cabinet_height / 2
        location = (x, y, z)

        obj = bpy.ops.mesh.primitive_cube_add(size=1)
        frame = bpy.context.object
        frame.name = name_prefix
        frame.scale = scale
        frame.location = location
        frame.parent = parent_obj  # Parent to the main object
        frame_objects.append(frame)

    @staticmethod
    def create_rail(parent_obj, location,name_prefix,scale,frame_objects,cabinet_height):
        x = float(0)
        y = float(location[1])
        z = location[2]
        location = (x,y,z)

        obj = bpy.ops.mesh.primitive_cube_add(size=1)
        frame = bpy.context.object
        frame.name = name_prefix
        frame.scale = scale
        frame.location =location
        frame.parent = parent_obj  # Parent to the main object
        frame_objects.append(frame)

    @staticmethod
    def create_kitchen_counter(name_prefix, start_node, end_node, cabinet_type="base",
                               cabinet_height=0.9, cabinet_depth=0.6,
                               frame_spec={"thickness": 0.04, "width": 0.04},
                               add_countertop=True, countertop_thickness=0.05,
                               material_frame=None, material_counter=None,
                               cutout_type=None,z=0):
        """
        Creates a framed kitchen counter between start_node and end_node, with all parts parented to a single object.

        Parameters:
        - `name_prefix`: Base name for all objects.
        - `start_node`, `end_node`: (x, y, z) defining the span along the wall.
        - `cabinet_type`: "base" or "upper".
        - `cabinet_height`, `cabinet_depth`: Overall dimensions.
        - `frame_spec`: Dictionary with framing material thickness and width.
        - `add_countertop`: If True, a countertop is added.
        - `cutout_type`: "sink", "dishwasher", or None for normal cabinets.
        """

        # Convert nodes to vectors
        start_vec = Vector(start_node)
        end_vec = Vector(end_node)

        # Compute width (length of counter along the wall)
        direction = end_vec - start_vec
        cabinet_width = direction.length
        direction.normalize()

        # Compute angle for rotation
        if abs(direction.x) > abs(direction.y):  # Wall is mostly along X-axis
            rotation_angle = 0 if direction.x > 0 else math.radians(180)
        else:  # Wall is mostly along Y-axis
            rotation_angle = math.radians(90) if direction.y > 0 else math.radians(-90)

        # Compute depth direction (perpendicular to the wall)
        up_vec = Vector((0, 0, 1))
        depth_dir = direction.cross(up_vec)
        depth_dir.normalize()
        center = (start_vec + end_vec) /2
        x = center[0]
        y = center[1]
        # Create a parent object (Empty) to group all parts
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=(x,y,z))
        parent_obj = bpy.context.object
        parent_obj.name = f"{name_prefix}_Parent"
        # Rotate parent based on the calculated angle
        parent_obj.rotation_euler.z = rotation_angle
        #bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
        # All child objects will be positioned relative to this parent
        local_origin = Vector((0, 0, 0))  # Local space for children

        # Extract framing specs
        frame_thickness = frame_spec["thickness"]
        frame_width = frame_spec["width"]

        # **Frame Structure**
        frame_objects = []

        half_width = float(cabinet_width / 2)
        half_depth = float(cabinet_depth/2)
        # Define frame corner positions relative to parent
        back_left_bottom = (-half_width,-half_depth, float(0))
        back_right_bottom = (cabinet_width/2, -half_depth, float(0))
        front_left_bottom = (-cabinet_width/2, half_depth, float(0))
        front_right_bottom = (cabinet_width/2, half_depth, float(0))

        back_left_top = (back_left_bottom[0], back_left_bottom[1], float(cabinet_height))
        back_right_top = (back_right_bottom[0], back_right_bottom[1], float(cabinet_height))
        front_left_top = (front_left_bottom[0], front_left_bottom[1], float(cabinet_height))
        front_right_top = (front_right_bottom[0], front_right_bottom[1], float(cabinet_height))

        positions=[]

        positions.append(back_left_bottom)
        positions.append(back_right_bottom)
        positions.append(front_left_bottom)
        positions.append(front_right_bottom)

        scale = (frame_thickness, frame_width, cabinet_height)
        for i,p in enumerate(positions):
           name = f"{name_prefix}_Post_{i}"
           KitchenCounterFactory.create_post(parent_obj, p,name, scale,frame_objects,cabinet_height)

        positions = []

        positions.append(back_left_bottom)
        positions.append(back_left_top)
        positions.append(front_left_top)
        positions.append(front_left_bottom)

        scale = (cabinet_width , frame_thickness , frame_thickness )
        for i, p in enumerate(positions):
            name = f"{name_prefix}_Rail_{i}"
            KitchenCounterFactory.create_rail(parent_obj, p, name, scale, frame_objects, cabinet_width)

        # **Add Countertop (if applicable)**
        if cabinet_type == "base" and add_countertop:
            bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, cabinet_height))
            countertop = bpy.context.object
            countertop.name = f"{name_prefix}_Countertop"
            countertop.scale = (cabinet_width , cabinet_depth , countertop_thickness / 2)
            countertop.parent = parent_obj
            if material_counter:
                countertop.data.materials.append(bpy.data.materials.get(material_counter))
            #parent,name="Bathtub", size=(1.524, 1, .6),location=(0,0,0), wall_thickness=0.9, bevel_width=0.3, subsurf_levels=2
            BassinFactory.create_bassin(parent_obj,"sink",(.8,.5,.35),(0,0,.78),.9,.3,2)

        # **Cabinet Doors**
        door_count = max(1, int(cabinet_width / 0.6))  # One door per ~60cm
        door_width = cabinet_width / door_count

        for i in range(door_count):
            bpy.ops.mesh.primitive_cube_add(size=1,
                                            location=(door_width * (i + 0.5)-cabinet_width/2, -cabinet_depth / 2, cabinet_height / 2))
            door = bpy.context.object
            door.name = f"{name_prefix}_Door_{i}"
            door.scale = (door_width  - 0.02, frame_thickness / 2, (cabinet_height - 0.1))
            door.parent = parent_obj
            if material_frame:
                door.data.materials.append(bpy.data.materials.get(material_frame))

        # **Return the parent object**
        return parent_obj


def main():
    """Main function to generate a kitchen counter in Blender."""

    # Check if running in Blender
    if not bpy.context.scene:
        print("❌ This script must be run inside Blender.")
        return

    # Define materials
    materials = {
        "countertop": "StoneMaterial",
        "frame": "WoodMaterial"
    }

    # Define frame specs
    frame_spec = {
        "thickness": 0.038,  # Approx 1.5 inches (2x2)
        "width": 0.038
    }

    # Define counter segment
    start_node = (-4.85033 , 1.51895, 0)
    end_node = (-4.85033, 4.12016 , 0)

    # Create the counter
    KitchenCounterFactory.create_kitchen_counter(
        name_prefix="KitchenCounter",
        start_node=start_node,
        end_node=end_node,
        cabinet_type="base",
        cabinet_height=0.9,
        cabinet_depth=0.6,
        frame_spec=frame_spec,
        add_countertop=True,
        countertop_thickness=0.04,
        material_frame=materials["frame"],
        material_counter=materials["countertop"]
    )
    # Create the upper cabinet
    KitchenCounterFactory.create_kitchen_counter(
        name_prefix="UpperCabinet",
        start_node=start_node,
        end_node=end_node,
        cabinet_type="upper",
        cabinet_height=0.75,
        cabinet_depth=0.35,
        frame_spec=frame_spec,
        add_countertop=False,
        material_frame=materials["frame"],
        z=1.3716
    )


# Run the script
if __name__ == "__main__":
    main()
