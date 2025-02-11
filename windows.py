# -------------------------------------------------------------------
# OPTIONAL WINDOW CREATION: Header, sill, jack studs
# -------------------------------------------------------------------
import bpy
from mathutils import Vector
from board_factory import *
class WindowFactory:
    @staticmethod
    def cut_window_opening(window,wall_structure, name_prefix, window_bottom_z,
                           window_width, window_height, bottom_plate_height, stud_spec):
        """
        Cuts a correctly-sized window opening in either:
        - A collection of objects (cladding, studs, etc.).
        - A single object with child objects.

        The function automatically applies Boolean operations to create the hole.

        Args:
            wall_structure: A collection OR a parent object with children.
            name_prefix: Prefix for object names.
            window_center_x: X-coordinate of the window center.
            window_bottom_z: Z-coordinate of the window bottom.
            window_width: Width of the window.
            window_height: Height of the window.
            bottom_plate_height: Height of the bottom plate.

        Returns:
            True if the cutout was successfully applied, False otherwise.
        """
        #"2x6": {"thickness": 0.0381, "width": 0.1397}
        thickness = stud_spec["thickness"]
        width = stud_spec["width"]
        # **STEP 1: Detect Wall Components (Collection or Object with Children)**
        wall_objects = []

        if isinstance(wall_structure, bpy.types.Collection):  # If it's a collection
            wall_objects = [obj for obj in wall_structure.objects if obj.type == 'MESH']

        elif isinstance(wall_structure, bpy.types.Object) and wall_structure.type == 'MESH':  # If it's a single object
            wall_objects.append(wall_structure)

        elif isinstance(wall_structure, bpy.types.Object):  # If it's a parent object with children
            wall_objects = [child for child in wall_structure.children if child.type == 'MESH']

        else:
            print("❌ Error: Invalid wall structure provided.")
            return False

        if not wall_objects:
            print("❌ Error: No valid wall components found.")
            return False
        wall_structure

        # **STEP 1: Compute the Relative Position (Offset from Wall)**
        relative_position = Vector((
            0,
            0.0,  # Y remains zero
            float(bottom_plate_height + window_bottom_z + (window_height / 2))
        ))

        # **STEP 2: Convert Wall Location to Vector**
        wall_position_v = Vector((
            float(wall_structure.location.x),
            float(wall_structure.location.y),
            float(wall_structure.location.z)
        ))

        # **STEP 3: Compute the Final Cutout Position**
        cutout_position = wall_position_v + relative_position
        # **STEP 2: Create the Cutout Object with Correct Dimensions**
        bpy.ops.mesh.primitive_cube_add(
            size=1,
            location=(0,0,float(bottom_plate_height + window_bottom_z + (window_height / 2)))
        )
        cutout_obj = bpy.context.object
        cutout_obj.name = f"{name_prefix}_WindowCutout"
        cutout_obj.parent = window
        # ✅ **STEP 2: Increase the Cutout Size for the Frame**
        #"2x6": {"thickness": 0.0381, "width": 0.1397}
        frame_width = thickness * 2
        total_window_width = window_width + frame_width  # Add space for frame
        total_window_height = window_height + frame_width  # Add space for frame

        # ✅ **Explicitly Set Dimensions Instead of Scale**
        cutout_obj.dimensions = (
            total_window_width,  # Full width of the window
            width*2,  # Depth (ensure it cuts through all wall layers)
            total_window_height  # Full height of the window
        )

        # Apply the transformation to lock in dimensions
        bpy.ops.object.transform_apply(scale=True, location=False)

        print(
            f"✅ Created window cutout: {cutout_obj.name} at X={0}, Z={bottom_plate_height + window_bottom_z}")

        # **STEP 3: Apply Boolean Cut to Each Wall Component**
        success = False
        for obj in wall_objects:
            if obj.type == 'MESH':  # Only apply to mesh objects
                if obj.data is None or len(obj.data.polygons) == 0:
                    print(f"⚠️ Warning: {obj.name} is not a valid mesh. Skipping.")
                    continue

                boolean_mod = obj.modifiers.new(name="Window_Cut", type='BOOLEAN')
                boolean_mod.object = cutout_obj
                boolean_mod.operation = 'DIFFERENCE'

                bpy.context.view_layer.objects.active = obj
                bpy.ops.object.modifier_apply(modifier=boolean_mod.name)

                print(f"✅ Applied Boolean cut to {obj.name}")
                success = True

        # Delete the cutout object after applying the cut
        bpy.data.objects.remove(cutout_obj)

        return success

    @staticmethod
    def create_king_studs(
            name_prefix,
            window_width,
            bottom_plate_height,
            top_plate_height,
            second_top_plate_height,
            stud_spec,
            wall_height,
            material=None,
            parent=None
    ):
        """
        Creates full-height King Studs on both sides of a window opening.

        Args:
            name_prefix (str): Prefix for object names.
            window_center_x (float): X position of the window center.
            window_width (float): Width of the window opening.
            bottom_plate_height (float): Height of the bottom plate.
            top_plate_height (float): Thickness of the top plate.
            second_top_plate_height (float): Thickness of the second top plate (if present).
            stud_size (dict): Dictionary containing stud dimensions (thickness, width, height).
            wall_height (float): Total height of the wall.
            material (bpy.types.Material, optional): Material to apply to the king studs.
            parent (bpy.types.Object, optional): Parent object for the king studs.

        Returns:
            List[bpy.types.Object]: The created King Stud objects.
        """

        # **STEP 1: Compute King Stud Height**
        king_stud_height = wall_height - (top_plate_height + second_top_plate_height)
        thickness = stud_spec["thickness"]
        width = stud_spec["width"]
        center_w = window_width / 2.0
        # **STEP 2: Compute King Stud Positions**
        left_x = -center_w - (thickness / 2.0)
        right_x = center_w + (thickness / 2.0)

        # **STEP 3: Create King Studs (Double for Extra Strength)**
        king_studs = []
        for i in range(2):  # Two king studs per side
            left_king_x = left_x - thickness - (i * thickness)
            right_king_x = right_x + thickness + (i * thickness)

            # Left King Stud
            lk = BoardFactory.add_board(parent,
                                        board_name=f"{name_prefix}_KingStudLeft_{i + 1}",
                                        length=thickness,
                                        height=king_stud_height,
                                        depth=width,
                                        location=(left_king_x, 0, bottom_plate_height + king_stud_height / 2.0),
                                        material=material
                                        )
            # if parent:
            #    lk.parent = parent
            king_studs.append(lk)

            # Right King Stud
            rk = BoardFactory.add_board(parent,
                                        board_name=f"{name_prefix}_KingStudRight_{i + 1}",
                                        length=thickness,
                                        height=king_stud_height,
                                        depth=width,
                                        location=(right_king_x, 0, bottom_plate_height + king_stud_height / 2.0),
                                        material=material
                                        )
            # if parent:
            #    rk.parent = parent
            king_studs.append(rk)

        print(f"✅ Created {len(king_studs)} King Studs for {name_prefix}")

        return king_studs

    @staticmethod
    def create_lintel(
            name_prefix,
            window_width,
            bottom_plate_height,
            window_bottom_z,
            window_height,
            wall_height,
            top_plate_height,
            second_top_plate_height,
            stud_spec,
            is_load_bearing=True,
            material=None,
            parent=None
    ):
        """
        Creates a properly sized lintel (header) above a window opening, following Canadian NBC standards.

        Args:
            name_prefix (str): Prefix for object names.
            window_center_x (float): X position of the window center.
            window_width (float): Width of the window opening.
            bottom_plate_height (float): Height of the bottom plate.
            window_bottom_z (float): Bottom of the window opening.
            window_height (float): Height of the window opening.
            wall_height (float): Total height of the wall.
            top_plate_height (float): Thickness of the top plate.
            second_top_plate_height (float): Thickness of the second top plate (if present).
            stud_size (dict): Dictionary containing stud dimensions (thickness, width, height).
            is_load_bearing (bool): Whether the wall is load-bearing or not.
            material (bpy.types.Material): Material to apply to the lintel.
            parent (bpy.types.Object, optional): Parent object for the lintel.

        Returns:
            bpy.types.Object: The created lintel object.
        """

        # **STEP 1: Choose the Correct Lintel Size (NBC Standard)**
        if window_width <= 1.2:  # ≤ 4ft window
            lintel_height = 0.140  # (2) 2x4 stacked or 2x6
        elif 1.2 < window_width <= 1.8:  # 4-6ft window
            lintel_height = 0.190 if is_load_bearing else 0.140  # (2) 2x6 for load-bearing, or (1) 2x6
        elif 1.8 < window_width <= 2.4:  # 6-8ft window
            lintel_height = 0.240 if is_load_bearing else 0.190  # (2) 2x8 or (2) 2x6
        elif 2.4 < window_width <= 3.0:  # 8-10ft window
            lintel_height = 0.300 if is_load_bearing else 0.240  # LVL 2x10 or (2) 2x8
        else:  # >10ft windows
            lintel_height = 0.350  # LVL beam or Steel Beam

        # **STEP 2: Compute the Lintel Position**
        #"2x6": {"thickness": 0.0381, "width": 0.1397}
        header_width = stud_spec["width"]
        thickness = stud_spec["thickness"]
        header_z = bottom_plate_height + window_bottom_z + window_height
        max_header_z = wall_height - (top_plate_height + second_top_plate_height + lintel_height)
        if header_z > max_header_z:
            header_z = max_header_z

        pos = Vector((0, 0, header_z + thickness + lintel_height / 2.0))
        # **STEP 3: Create the Lintel**
        lintel = BoardFactory.add_board(parent,
                                        board_name=f"{name_prefix}_Lintel",
                                        length=window_width + (thickness * 2),  # Extend over jack studs
                                        height=lintel_height,
                                        depth=header_width,
                                        location=pos,
                                        material=material
                                        )

        # if parent:
        #    lintel.parent = parent  # Attach to window parent

        print(f"✅ Created lintel: {lintel.name} | Height: {lintel_height:.3f}m | Load-Bearing: {is_load_bearing}")

        return lintel

    @staticmethod
    def create_window_opening(
            wall,
            name_prefix,
            window_center_x,
            window_bottom_z,
            window_width,
            window_height,
            bottom_plate_height,
            top_plate_height,
            stud_spec,
            wall_height,
            second_top_plate_height=0.0381,
            material=None,
            wall_ll=None,
            glass_material=None
    ):
        """
        Creates a minimal window framing: a header, sill, and left/right jack studs
        within the total 'wall_height'.
        """
        # **STEP 1: Log the Wall's Position and Transformation Matrix**
        print(f"🔎 Wall Name: {wall.name}")
        print(f"📍 Wall Location (Global): {wall.location}")
        print(f"🛠️ Wall Matrix World: \n{wall.matrix_world}")
        thickness = stud_spec["thickness"]
        header_width = stud_spec["width"]  # ~0.0889

        # For simplicity, we'll assume one 2×4 thick header (on edge).
        header_thickness = thickness  # ~0.0381

        # The top of the window opening is at (window_bottom_z + window_height).
        # We'll place the header's bottom at that point, or clamp if near top plates.
        header_z = bottom_plate_height + window_bottom_z + window_height
        # **STEP 1: Create the Parent Wall Object**
        bpy.ops.object.empty_add(type='PLAIN_AXES')
        window_parent = bpy.context.object
        window_parent.name = f"{wall.name}_Window"
        window_parent.parent = wall
        window_parent.location = (window_center_x,0,0)
        # **STEP 1: Cut the Window Opening**
        cut_success = WindowFactory.cut_window_opening(window_parent,
            wall, name_prefix, window_bottom_z,
            window_width, window_height, bottom_plate_height, stud_spec)
        if not cut_success:
            print("❌ Window opening failed. Aborting window creation.")
            return

        is_load_bearing = False
        lintel = WindowFactory.create_lintel(
            name_prefix=name_prefix,
            window_width=window_width,
            bottom_plate_height=bottom_plate_height,
            window_bottom_z=window_bottom_z,
            window_height=window_height,
            wall_height=wall_height,
            top_plate_height=top_plate_height,
            second_top_plate_height=second_top_plate_height,
            stud_spec=stud_spec,
            is_load_bearing=is_load_bearing,
            material=material,
            parent=window_parent)

        max_header_z = wall_height - (top_plate_height + second_top_plate_height + header_thickness)
        if header_z > max_header_z:
            header_z = max_header_z

        # **STEP 5: Add Full-Height King Studs (Now Using `create_king_studs`)**
        king_studs = WindowFactory.create_king_studs(
            name_prefix=name_prefix,
            window_width=window_width,
            bottom_plate_height=bottom_plate_height,
            top_plate_height=top_plate_height,
            second_top_plate_height=second_top_plate_height,
            stud_spec=stud_spec,
            wall_height=wall_height,
            material=material,
            parent=window_parent)
        #"2x6": {"thickness": 0.0381, "width": 0.1397}
        thickness = stud_spec["thickness"]
        depth = stud_spec["width"]
        full_width = window_width + thickness * 2
        header = BoardFactory.add_board(window_parent,
                                        board_name=f"{name_prefix}_Header",
                                        length=full_width,
                                        height=thickness,
                                        depth=depth,
                                        location=(0, 0, header_z + header_thickness / 2.0),
                                        material=material
                                        )

        # Sill: place a horizontal 2×4 at the bottom of the window
        sill_thickness = thickness
        sill_z = bottom_plate_height + window_bottom_z - sill_thickness
        if sill_z > bottom_plate_height:
            sill = BoardFactory.add_board(window_parent,
                                          board_name=f"{name_prefix}_Sill",
                                          length=full_width,
                                          height=thickness,
                                          depth=depth,
                                          location=(0, 0, sill_z + sill_thickness / 2.0),
                                          material=material
                                          )

        # Jack studs
        jack_height = header_z - bottom_plate_height
        half_width = window_width / 2.0
        half_thickness = thickness / 2.0
        if jack_height > 0:
            left_x =  - (half_width) - (half_thickness)
            right_x =  (half_width) + (half_thickness)

            lj = BoardFactory.add_board(
                window_parent,
                board_name=f"{name_prefix}_JackStudLeft",
                length=thickness,
                height=jack_height,
                depth=depth,
                location=(left_x, 0, bottom_plate_height + jack_height / 2.0),
                material=material
            )

            rj = BoardFactory.add_board(
                window_parent,
                board_name=f"{name_prefix}_JackStudRight",
                length=thickness,
                height=jack_height,
                depth=depth,
                location=(right_x, 0, bottom_plate_height + jack_height / 2.0),
                material=material
            )

        # **STEP 4: Create the Glass Pane**
        glass_thickness = 0.006  # 6mm thick glass
        glass_pane = BoardFactory.add_board(
            window_parent,
            board_name=f"{name_prefix}_Glass",
            length=window_width,
            height=window_height,
            depth=glass_thickness,
            location=(
                0, -glass_thickness / 2.0, bottom_plate_height + window_bottom_z + window_height / 2.0),
            material=glass_material
        )