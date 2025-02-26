# framing_factory.py

import bpy
from mathutils import Vector
from board_factory import BoardFactory

class FramingFactory:
    @staticmethod
    def cut_opening(
        opening_parent,
        wall_structure,
        name_prefix,
        bottom_z,
        opening_width,
        opening_height,
        bottom_plate_height,
        stud_spec
    ):
        """
        Generic method for cutting an opening (window or door) in a wall
        via a Boolean difference.

        Args:
            opening_parent (bpy.types.Object):
                The "parent" or main object for this opening (e.g. a new Empty).
            wall_structure (bpy.types.Object or bpy.types.Collection):
                The wall (or collection of wall pieces).
            name_prefix (str):
                A prefix for naming new objects/modifiers.
            bottom_z (float):
                Local Z offset where the opening starts above the bottom plate.
            opening_width (float):
                Width of the opening.
            opening_height (float):
                Height of the opening.
            bottom_plate_height (float):
                Thickness/height of the bottom plate above the floor.
            stud_spec (dict):
                e.g. {"thickness": 0.0381, "width": 0.1397}

        Returns:
            bool: True if successful, False otherwise.
        """
        thickness = stud_spec["thickness"]
        width = stud_spec["width"]

        # Identify mesh objects (either a single object, parent's children, or collection)
        wall_objects = []
        if isinstance(wall_structure, bpy.types.Collection):
            wall_objects = [obj for obj in wall_structure.objects if obj.type == 'MESH']
        elif isinstance(wall_structure, bpy.types.Object) and wall_structure.type == 'MESH':
            wall_objects.append(wall_structure)
        elif isinstance(wall_structure, bpy.types.Object):
            wall_objects = [child for child in wall_structure.children if child.type == 'MESH']

        if not wall_objects:
            print("❌ Error: No valid wall mesh objects found.")
            return False

        # Create a temporary 'cutout' cube that will do the Boolean difference
        cutout_center_z = bottom_plate_height + bottom_z + (opening_height / 2.0)
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(0, 0, cutout_center_z)
        )
        cutout_obj = bpy.context.object
        cutout_obj.name = f"{name_prefix}_OpeningCutout"
        cutout_obj.parent = opening_parent

        # Increase the dimension so it extends beyond the actual opening
        # e.g., add some thickness to create a rough opening
        frame_allowance = thickness
        cutout_obj.dimensions = (
            opening_width ,
            width * 2,                 # plenty of depth to cut through
            opening_height
        )
        bpy.ops.object.transform_apply(scale=True, location=False)

        # Apply Boolean difference for each wall mesh
        success = False
        for obj in wall_objects:
            if obj.type == 'MESH' and obj.data and len(obj.data.polygons) > 0:
                bool_mod = obj.modifiers.new(name=f"{name_prefix}_Cut", type='BOOLEAN')
                bool_mod.object = cutout_obj
                bool_mod.operation = 'DIFFERENCE'

                bpy.context.view_layer.objects.active = obj
                bpy.ops.object.modifier_apply(modifier=bool_mod.name)
                success = True
                print(f"✅ Applied opening cut to {obj.name}")

        # Remove temporary cutout
        bpy.data.objects.remove(cutout_obj, do_unlink=True)

        return success
    @staticmethod
    def create_header_spec(
        opening_width,
        bottom_plate_height,
        opening_bottom_z,
        opening_height,
        wall_height,
        top_plate_height,
        second_top_plate_height,
        stud_spec,
        is_load_bearing=True):

        thickness = stud_spec["thickness"]
        width = stud_spec["width"]

        # Decide header height (for demonstration)
        # For actual code, ensure compliance with your local code tables
        if opening_width <= 1.2:
            header_height = 0.140 if is_load_bearing else 0.089
        elif opening_width <= 1.8:
            header_height = 0.190 if is_load_bearing else 0.140
        else:
            header_height = 0.240 if is_load_bearing else 0.190

        # Position the header just above the top of the opening
        opening_top_z = bottom_plate_height + opening_bottom_z + opening_height
        max_header_z = wall_height - (top_plate_height + second_top_plate_height + header_height)
        if opening_top_z > max_header_z:
            opening_top_z = max_header_z

        header_z_center = opening_top_z + header_height / 2.0
        header_length = opening_width + thickness * 2.
        spec= {}

        spec["header_z_center"] = header_z_center
        spec["header_length"] = header_length
        spec["header_height"] = header_height
        spec["width"] = width

        return spec

    @staticmethod
    def create_header(
        name_prefix,
        header_spec,
        material=None,
        parent=None
    ):
        """
        Creates a lintel/header above the opening (door or window).

        Simple logic using 'opening_width' to pick an approximate
        header size. Adjust as needed for building code.

        Returns: The newly created header object.
        """
        header_length = header_spec["header_length"]
        header_height = header_spec["header_height"]
        width = header_spec["width"]
        header_z_center = header_spec["header_z_center"]
        header_obj = BoardFactory.add_board(
            parent=parent,
            board_name=f"{name_prefix}_Header",
            length=header_length,
            height=header_height,
            depth=width,
            location=(0, 0, header_z_center),
            material=material
        )
        print(f"✅ Created header: {header_obj.name} (Height={header_height:.3f}m)")
        return header_obj, header_z_center ,header_height

    @staticmethod
    def create_king_studs(
        name_prefix,
        opening_width,
        bottom_plate_height,
        top_plate_height,
        second_top_plate_height,
        stud_spec,
        wall_height,
        material=None,
        parent=None
    ):
        """
        Creates full-height king studs on both sides of the opening.
        """
        #"2x6": {"thickness": 0.0381, "width": 0.1397}
        thickness = stud_spec["thickness"]
        width = stud_spec["width"]
        top_frame_thickness =  (top_plate_height - second_top_plate_height)
        king_stud_height = wall_height
        half_opening = opening_width / 2.0

        # We'll place one king stud each side.
        left_x = -half_opening - (thickness*1.5)
        right_x = half_opening + (thickness*1.5)

        l_king = BoardFactory.add_board(
            parent,
            board_name=f"{name_prefix}_KingStudLeft",
            length=thickness,
            height=king_stud_height,
            depth=width,
            location=(left_x, 0, bottom_plate_height + king_stud_height / 2.0),
            material=material
        )
        r_king = BoardFactory.add_board(
            parent,
            board_name=f"{name_prefix}_KingStudRight",
            length=thickness,
            height=king_stud_height,
            depth=width,
            location=(right_x, 0, bottom_plate_height + king_stud_height / 2.0),
            material=material
        )
        print(f"✅ Created 2 king studs: {l_king.name} & {r_king.name}")
        return [l_king, r_king]

    @staticmethod
    def create_jack_studs(
        name_prefix,
        opening_width,
        bottom_plate_height,
        opening_bottom_z,
        opening_height,
        stud_spec,
        parent=None,
        material=None
    ):
        """
        Creates short jack studs under the header (if load-bearing),
        from floor (bottom plate) to top of opening.

        Usually used for windows or doors that have a header.
        """
        thickness = stud_spec["thickness"]
        width = stud_spec["width"]

        jack_stud_height = (
            (bottom_plate_height + opening_bottom_z + opening_height)
            - bottom_plate_height
        )
        if jack_stud_height <= 0:
            print("⚠️ No space for jack studs, skipping.")
            return []

        half_opening = opening_width / 2.0
        half_t = thickness / 2.0
        left_jack_x = -half_opening - half_t
        right_jack_x = half_opening + half_t

        l_jack = BoardFactory.add_board(
            parent,
            board_name=f"{name_prefix}_JackStudLeft",
            length=thickness,
            height=jack_stud_height,
            depth=width,
            location=(left_jack_x, 0, bottom_plate_height + jack_stud_height / 2.0),
            material=material
        )
        r_jack = BoardFactory.add_board(
            parent,
            board_name=f"{name_prefix}_JackStudRight",
            length=thickness,
            height=jack_stud_height,
            depth=width,
            location=(right_jack_x, 0, bottom_plate_height + jack_stud_height / 2.0),
            material=material
        )
        print(f"✅ Created jack studs: {l_jack.name}, {r_jack.name}")
        return [l_jack, r_jack]