import bpy

from furnitures_gen.cutout_util import CutoutUtil


class BassinFactory:
    @staticmethod
    def create_bassin(parent,name="Bathtub", size=(1.524, 1, .6),location=(0,0,1), wall_thickness=0.9, bevel_width=0.3, subsurf_levels=2):
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
        bathtub.location = location
        bathtub.scale = size
        bathtub.parent = parent
        bpy.context.view_layer.objects.active = bathtub
        #bpy.ops.object.transform_apply(scale=True, location=True)

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
        world_position = bathtub.matrix_world.translation
        world_rotation_euler = bathtub.matrix_world.to_euler()
        inner_cube.rotation_euler = world_rotation_euler
        print("World Position:", world_position)
        #(inner_size[2] / 2)
        inner_cube.location = (world_position[0], world_position[1], .8)
        #inner_cube.location = (5,5,1)
        inner_cube.scale = (.1, 1, .6)
        #bpy.ops.object.transform_apply(scale=True, location=True)

        # Add a bevel modifier to the inner cube to round its edges
        bevel_mod = inner_cube.modifiers.new(name="Bevel", type='BEVEL')
        bevel_mod.width = bevel_width/2
        bevel_mod.segments = 10

        # Apply the bevel modifier
        bpy.ops.object.select_all(action='DESELECT')
        inner_cube.select_set(True)
        #inner_cube.location = (0, 0, .5)
        bpy.context.view_layer.objects.active = inner_cube
        bpy.ops.object.modifier_apply(modifier=bevel_mod.name)

        # Delete the inner cube
        bpy.ops.object.select_all(action='DESELECT')
        inner_cube.select_set(True)
        #bpy.ops.object.delete()

        # Add a bevel modifier to the bathtub for smooth edges
        bevel_mod = bathtub.modifiers.new(name="Bevel", type='BEVEL')
        bevel_mod.width = 0.1
        bevel_mod.segments = 6
        bpy.ops.object.select_all(action='DESELECT')
        bathtub.select_set(True)
        bpy.context.view_layer.objects.active = bathtub
        bpy.ops.object.modifier_apply(modifier=bevel_mod.name)

        CutoutUtil.cuttout_util(inner_cube, parent)

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
        # BathThubFactory.create_faucet(name=f"{name}_Faucet", position=(0, size[1] / 2 + 0.05, size[2] + 0.1))
        print(f"{name} created successfully!")
        return bathtub