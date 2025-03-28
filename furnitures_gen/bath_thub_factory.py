import bpy
import math
import bmesh
import bpy
import math
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


class BathThubFactory:

    @staticmethod
    def create_faucet(name="Faucet", position=(0, 0, 0), base_radius=0.1, spout_radius=0.05, height=0.3,
                      spout_length=0.2):
        """
        Creates a faucet using two vertical cylinders, where the inner cylinder has a semi-circular extruded spout.

        Parameters:
        - name (str): Name of the faucet object.
        - position (tuple): Position of the faucet base.
        - base_radius (float): Radius of the larger outer faucet body.
        - spout_radius (float): Radius of the inner spout.
        - height (float): Height of the faucet base.
        - spout_length (float): Length before curving into a semi-circle.
        """

        # Create the larger outer faucet body
        bpy.ops.mesh.primitive_cylinder_add(radius=base_radius, depth=height, location=position)
        outer_faucet = bpy.context.object
        outer_faucet.name = f"{name}_Outer"

        # Create the inner spout base (smaller vertical cylinder, centered)
        inner_pos = (position[0], position[1], position[2] + height / 2)  # Centered on top of the larger one
        bpy.ops.mesh.primitive_cylinder_add(radius=spout_radius, depth=height, location=inner_pos)
        inner_spout = bpy.context.object
        inner_spout.name = f"{name}_Inner"

        # Switch to Edit Mode to modify the inner spout
        bpy.ops.object.select_all(action='DESELECT')
        inner_spout.select_set(True)
        bpy.context.view_layer.objects.active = inner_spout
        bpy.ops.object.mode_set(mode='EDIT')

        # Get mesh data
        mesh = bmesh.from_edit_mesh(inner_spout.data)

        # Find the topmost face
        max_z = max(v.co.z for v in mesh.verts)  # Get the highest Z value
        top_faces = [f for f in mesh.faces if all(v.co.z == max_z for v in f.verts)]

        if not top_faces:
            print("Error: Could not find top face.")
            bpy.ops.object.mode_set(mode='OBJECT')
            return

        # Select only the top face
        for f in mesh.faces:
            f.select = False  # Deselect all faces
        top_face = top_faces[0]
        for vert in top_face.verts:
            vert.select = True  # Select the top vertices

        # Move the 3D cursor to the correct radius for smooth spinning
        cursor_offset = spout_radius + spout_length / 2  # Place at the correct arc radius
        bpy.context.scene.cursor.location = (position[0] + cursor_offset, position[1], position[2] + height / 2)

        # Extrude the face slightly before spinning to extend outward first
        bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={"value": (spout_length / 6, 0, 0)})

        # Spin to form a semi-circle extrusion
        bpy.ops.mesh.spin(steps=12, angle=math.radians(180), center=bpy.context.scene.cursor.location, axis=(0, 1, 0))

        # Exit Edit Mode
        bpy.ops.object.mode_set(mode='OBJECT')

        # Join outer faucet and inner spout
        bpy.ops.object.select_all(action='DESELECT')
        outer_faucet.select_set(True)
        inner_spout.select_set(True)
        bpy.context.view_layer.objects.active = outer_faucet
        bpy.ops.object.join()

        print(f"{name} created successfully!")
        return outer_faucet

    @staticmethod
    def create_thub(name="Bathtub", size=(1.524, 1, .6), wall_thickness=0.9, bevel_width=0.3, subsurf_levels=2):
        """
        Prototype Factory Method to create a bathtub in Blender.

        Parameters:
        - name (str): Name of the bathtub object.
        - size (tuple): Dimensions (length, width, height) of the outer bathtub.
        - inner_size (tuple): Dimensions of the cutout area inside the bathtub.
        - wall_thickness (float): Thickness of the bathtub walls.
        - bevel_width (float): Bevel width for smoother edges.
        - subsurf_levels (int): Number of subdivision levels for smoother geometry.

        Returns:
        - bpy.types.Object: The created bathtub object.
        """
        inner_size = (size[0] - 2 * wall_thickness, size[1] - 2 * wall_thickness, size[2] - wall_thickness)
        # Create the base cube for the bathtub
        bpy.ops.mesh.primitive_cube_add(size=1)
        bathtub = bpy.context.object
        bathtub.name = name
        bathtub.location = (0, 0, size[2] / 2)
        bathtub.scale = size
        bpy.context.view_layer.objects.active = bathtub
        bpy.ops.object.transform_apply(scale=True, location=True)

        # bpy.ops.transform.resize(value=size)

        # Subdivide the bathtub mesh for better smoothing
        bpy.ops.object.select_all(action='DESELECT')
        bathtub.select_set(True)
        bpy.context.view_layer.objects.active = bathtub
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.subdivide(number_cuts=8)
        bpy.ops.object.mode_set(mode='OBJECT')

        # Create the inner cube for the cutout
        bpy.ops.mesh.primitive_cube_add(size=1)
        inner_cube = bpy.context.object
        inner_cube.name = f"{name}_InnerCube"
        inner_cube.location = (0, 0, inner_size[2] / 2)
        inner_cube.scale = size
        bpy.ops.object.transform_apply(scale=True, location=True)

        # Add a bevel modifier to the inner cube to round its edges
        bevel_mod = inner_cube.modifiers.new(name="Bevel", type='BEVEL')
        bevel_mod.width = bevel_width
        bevel_mod.segments = 10

        # Apply the bevel modifier
        bpy.ops.object.select_all(action='DESELECT')
        inner_cube.select_set(True)
        inner_cube.location = (0, 0, .5)
        bpy.context.view_layer.objects.active = inner_cube
        bpy.ops.object.modifier_apply(modifier=bevel_mod.name)

        # Add a Boolean modifier to the bathtub to subtract the beveled inner cube
        bool_mod = bathtub.modifiers.new(name="BoolCut", type='BOOLEAN')
        bool_mod.object = inner_cube
        bool_mod.operation = 'DIFFERENCE'

        # Apply the Boolean modifier
        bpy.ops.object.select_all(action='DESELECT')
        bathtub.select_set(True)
        bpy.context.view_layer.objects.active = bathtub
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)

        # Delete the inner cube
        bpy.ops.object.select_all(action='DESELECT')
        inner_cube.select_set(True)
        bpy.ops.object.delete()

        # Add a bevel modifier to the bathtub for smooth edges
        bevel_mod = bathtub.modifiers.new(name="Bevel", type='BEVEL')
        bevel_mod.width = 0.1
        bevel_mod.segments = 6
        bpy.ops.object.select_all(action='DESELECT')
        bathtub.select_set(True)
        bpy.context.view_layer.objects.active = bathtub
        bpy.ops.object.modifier_apply(modifier=bevel_mod.name)

        # Add a subdivision surface modifier for smooth geometry
        subsurf_mod = bathtub.modifiers.new(name="Subsurf", type='SUBSURF')
        subsurf_mod.levels = subsurf_levels
        bpy.ops.object.select_all(action='DESELECT')
        bathtub.select_set(True)
        bpy.context.view_layer.objects.active = bathtub
        bpy.ops.object.modifier_apply(modifier=subsurf_mod.name)

        # Set shading to smooth
        bpy.ops.object.select_all(action='DESELECT')
        bathtub.select_set(True)
        bpy.ops.object.shade_smooth()

        # Move the bathtub to the origin
        # bpy.ops.object.select_all(action='DESELECT')
        # bathtub.select_set(True)
        # bpy.context.view_layer.objects.active = bathtub
        # bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
        # bpy.ops.object.location_clear()
        #BathThubFactory.create_faucet(name=f"{name}_Faucet", position=(0, size[1] / 2 + 0.05, size[2] + 0.1))
        print(f"{name} created successfully!")
        return bathtub


if __name__ == "__main__":
    BathThubFactory.create_thub()