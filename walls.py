import bpy
import math
from mathutils import Vector


# -------------------------------------------------------------------
# MATERIALS (simple placeholders)
# -------------------------------------------------------------------
class MaterialFactory:
    @staticmethod
    def create_wood_material(name="FramingWood"):
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (0.8, 0.6, 0.4, 1.0)
            bsdf.inputs["Roughness"].default_value = 0.5
        return mat

    @staticmethod
    def create_sheathing_material(name="SheathingOSB"):
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (0.7, 0.6, 0.4, 1.0)
            bsdf.inputs["Roughness"].default_value = 0.7
        return mat

    @staticmethod
    def create_drywall_material(name="Drywall"):
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (0.9, 0.9, 0.9, 1.0)
            bsdf.inputs["Roughness"].default_value = 0.8
        return mat

    @staticmethod
    def create_simple_wood_material(name="Wood"):
        """
        Creates a simple brownish 'wood' material (non-procedural).
        """
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs["Base Color"].default_value = (0.6, 0.4, 0.2, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.5
        return mat

    @staticmethod
    def create_procedural_material(name, material_type):
        """
        Creates a procedural material ('wood', 'earth', or 'glass') for demonstration.
        """
        material = bpy.data.materials.new(name)
        material.use_nodes = True
        nodes = material.node_tree.nodes
        links = material.node_tree.links

        # Clear out the default nodes
        for node in nodes:
            nodes.remove(node)

        # Principled BSDF ShaderNodeBsdfPrincipled
        bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
        bsdf.location = (0, 0)
        # Material Output
        output = nodes.new(type='ShaderNodeOutputMaterial')
        output.location = (200, 0)
        links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

        # Choose material type
        if material_type == "wood":
            noise = nodes.new(type='ShaderNodeTexNoise')
            noise.inputs["Scale"].default_value = 10.0
            color_ramp = nodes.new(type='ShaderNodeValToRGB')
            color_ramp.color_ramp.elements[0].color = (0.6, 0.4, 0.2, 1)
            color_ramp.color_ramp.elements[1].color = (0.8, 0.6, 0.4, 1)
            links.new(noise.outputs["Fac"], color_ramp.inputs["Fac"])
            links.new(color_ramp.outputs["Color"], bsdf.inputs["Base Color"])
            bsdf.inputs["Roughness"].default_value = 0.7

        elif material_type == "earth":
            noise = nodes.new(type='ShaderNodeTexNoise')
            noise.inputs["Scale"].default_value = 20.0
            color_ramp = nodes.new(type='ShaderNodeValToRGB')
            color_ramp.color_ramp.elements[0].color = (0.4, 0.3, 0.2, 1)
            color_ramp.color_ramp.elements[1].color = (0.6, 0.5, 0.4, 1)
            links.new(noise.outputs["Fac"], color_ramp.inputs["Fac"])
            links.new(color_ramp.outputs["Color"], bsdf.inputs["Base Color"])
            bsdf.inputs["Roughness"].default_value = 0.9

        elif material_type == "glass":
            tree = material.node_tree
            material.blend_method = 'BLEND'
            material.shadow_method = 'HASHED'

            # Delete the Principled BSDF
            tree.nodes.remove(bsdf)  # Remove the old node by its reference (bsdf)

            # Create the Glass BSDF
            bsdf = tree.nodes.new('ShaderNodeBsdfGlass')  # Create a new bsdf node
            bsdf.location = (0, 0)

            bsdf.inputs["Color"].default_value = (0.8, 0.9, 1, 0.5)
            bsdf.inputs["IOR"].default_value = 1.45
            bsdf.inputs["Roughness"].default_value = 0.05

            tree.links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])  # Reconnect the output

        return material

    @staticmethod
    def create_materials():
        mat_framing = MaterialFactory.create_wood_material("FramingWood")
        mat_sheathing = MaterialFactory.create_sheathing_material("SheathingOSB")
        mat_drywall = MaterialFactory.create_drywall_material("Drywall")
        mat_glass = MaterialFactory.create_procedural_material("glass", "glass")
        materials = {}
        materials['framing'] = mat_framing
        materials['sheathing'] = mat_sheathing
        materials['drywall'] = mat_drywall
        materials['glass'] = mat_glass
        return materials


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
                  bevel_width=0.01, bevel_segments=3):
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

        return obj


# -------------------------------------------------------------------
# OPTIONAL WINDOW CREATION: Header, sill, jack studs
# -------------------------------------------------------------------
class WindowFactory:
    @staticmethod
    def cut_window_opening(wall_structure, name_prefix, window_center_x, window_bottom_z,
                           window_width, window_height, bottom_plate_height, frame_thickness):
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
        # **STEP 1: Compute the Relative Position (Offset from Wall)**
        relative_position = Vector((
            float(window_center_x),
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
            location=cutout_position
        )
        cutout_obj = bpy.context.object
        cutout_obj.name = f"{name_prefix}_WindowCutout"
        # ✅ **STEP 2: Increase the Cutout Size for the Frame**
        total_window_width = window_width + (frame_thickness * 2)  # Add space for frame
        total_window_height = window_height + (frame_thickness * 2)  # Add space for frame

        # ✅ **Explicitly Set Dimensions Instead of Scale**
        cutout_obj.dimensions = (
            total_window_width,  # Full width of the window
            2.0,  # Depth (ensure it cuts through all wall layers)
            total_window_height  # Full height of the window
        )

        # Apply the transformation to lock in dimensions
        bpy.ops.object.transform_apply(scale=True, location=False)

        print(
            f"✅ Created window cutout: {cutout_obj.name} at X={window_center_x}, Z={bottom_plate_height + window_bottom_z}")

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
        # bpy.data.objects.remove(cutout_obj)

        return success

    @staticmethod
    def create_king_studs(
            name_prefix,
            window_center_x,
            window_width,
            bottom_plate_height,
            top_plate_height,
            second_top_plate_height,
            stud_size,
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

        # **STEP 2: Compute King Stud Positions**
        left_x = window_center_x - (window_width / 2.0) - (stud_size["thickness"] / 2.0)
        right_x = window_center_x + (window_width / 2.0) + (stud_size["thickness"] / 2.0)

        # **STEP 3: Create King Studs (Double for Extra Strength)**
        king_studs = []
        for i in range(2):  # Two king studs per side
            left_king_x = left_x - stud_size["thickness"] - (i * stud_size["thickness"])
            right_king_x = right_x + stud_size["thickness"] + (i * stud_size["thickness"])

            # Left King Stud
            lk = BoardFactory.add_board(parent,
                                        board_name=f"{name_prefix}_KingStudLeft_{i + 1}",
                                        length=stud_size["thickness"],
                                        height=king_stud_height,
                                        depth=stud_size["width"],
                                        location=(left_king_x, 0, bottom_plate_height + king_stud_height / 2.0),
                                        material=material
                                        )
            # if parent:
            #    lk.parent = parent
            king_studs.append(lk)

            # Right King Stud
            rk = BoardFactory.add_board(parent,
                                        board_name=f"{name_prefix}_KingStudRight_{i + 1}",
                                        length=stud_size["thickness"],
                                        height=king_stud_height,
                                        depth=stud_size["width"],
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
            window_center_x,
            window_width,
            bottom_plate_height,
            window_bottom_z,
            window_height,
            wall_height,
            top_plate_height,
            second_top_plate_height,
            stud_size,
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
        header_width = stud_size["width"]
        header_z = bottom_plate_height + window_bottom_z + window_height
        max_header_z = wall_height - (top_plate_height + second_top_plate_height + lintel_height)
        if header_z > max_header_z:
            header_z = max_header_z

        pos = Vector((window_center_x, 0, header_z + lintel_height / 2.0))
        # **STEP 3: Create the Lintel**
        lintel = BoardFactory.add_board(parent,
                                        board_name=f"{name_prefix}_Lintel",
                                        length=window_width + (stud_size["thickness"] * 2),  # Extend over jack studs
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
            stud_size,
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

        # **STEP 1: Cut the Window Opening**
        cut_success = WindowFactory.cut_window_opening(
            wall, name_prefix, window_center_x, window_bottom_z,
            window_width, window_height, bottom_plate_height, STUD_THICKNESS)
        if not cut_success:
            print("❌ Window opening failed. Aborting window creation.")
            return

        # For simplicity, we'll assume one 2×4 thick header (on edge).
        header_thickness = stud_size["height"]  # ~0.0381
        header_width = stud_size["width"]  # ~0.0889

        # The top of the window opening is at (window_bottom_z + window_height).
        # We'll place the header's bottom at that point, or clamp if near top plates.
        header_z = bottom_plate_height + window_bottom_z + window_height
        # **STEP 1: Create the Parent Wall Object**

        bpy.ops.object.empty_add(type='PLAIN_AXES')
        window_parent = bpy.context.object
        window_parent.name = f"{wall.name}_Window"
        window_parent.parent = wall

        is_load_bearing = False
        lintel = WindowFactory.create_lintel(
            name_prefix=name_prefix,
            window_center_x=window_center_x,
            window_width=window_width,
            bottom_plate_height=bottom_plate_height,
            window_bottom_z=window_bottom_z,
            window_height=window_height,
            wall_height=wall_height,
            top_plate_height=top_plate_height,
            second_top_plate_height=second_top_plate_height,
            stud_size=stud_size,
            is_load_bearing=is_load_bearing,
            material=material,
            parent=window_parent)

        max_header_z = wall_height - (top_plate_height + second_top_plate_height + header_thickness)
        if header_z > max_header_z:
            header_z = max_header_z

        # **STEP 5: Add Full-Height King Studs (Now Using `create_king_studs`)**
        king_studs = WindowFactory.create_king_studs(
            name_prefix=name_prefix,
            window_center_x=window_center_x,
            window_width=window_width,
            bottom_plate_height=bottom_plate_height,
            top_plate_height=top_plate_height,
            second_top_plate_height=second_top_plate_height,
            stud_size=stud_size,
            wall_height=wall_height,
            material=material,
            parent=window_parent)

        header = BoardFactory.add_board(window_parent,
                                        board_name=f"{name_prefix}_Header",
                                        length=window_width + stud_size["thickness"] * 2,
                                        height=header_thickness,
                                        depth=header_width,
                                        location=(window_center_x, 0, header_z + header_thickness / 2.0),
                                        material=material
                                        )
        # header.parent = window_parent
        # move_to_collection(header, wall_coll)

        # Sill: place a horizontal 2×4 at the bottom of the window
        sill_thickness = stud_size["height"]
        sill_z = bottom_plate_height + window_bottom_z - sill_thickness
        if sill_z > bottom_plate_height:
            sill = BoardFactory.add_board(window_parent,
                                          board_name=f"{name_prefix}_Sill",
                                          length=window_width + stud_size["thickness"] * 2,
                                          height=sill_thickness,
                                          depth=stud_size["width"],
                                          location=(window_center_x, 0, sill_z + sill_thickness / 2.0),
                                          material=material
                                          )
            # sill.parent = window_parent
            # move_to_collection(sill, wall_coll)

        # Jack studs
        jack_height = header_z - bottom_plate_height
        if jack_height > 0:
            left_x = window_center_x - (window_width / 2.0) - (stud_size["thickness"] / 2.0)
            right_x = window_center_x + (window_width / 2.0) + (stud_size["thickness"] / 2.0)

            lj = BoardFactory.add_board(
                window_parent,
                board_name=f"{name_prefix}_JackStudLeft",
                length=stud_size["thickness"],
                height=jack_height,
                depth=stud_size["width"],
                location=(left_x, 0, bottom_plate_height + jack_height / 2.0),
                material=material
            )
            # lj.parent = window_parent
            # move_to_collection(lj, wall_coll)

            rj = BoardFactory.add_board(
                window_parent,
                board_name=f"{name_prefix}_JackStudRight",
                length=stud_size["thickness"],
                height=jack_height,
                depth=stud_size["width"],
                location=(right_x, 0, bottom_plate_height + jack_height / 2.0),
                material=material
            )
            rj.parent = window_parent
            # move_to_collection(rj, wall_coll)

        # **STEP 4: Create the Glass Pane**
        glass_thickness = 0.006  # 6mm thick glass
        glass_pane = BoardFactory.add_board(
            window_parent,
            board_name=f"{name_prefix}_Glass",
            length=window_width,
            height=window_height,
            depth=glass_thickness,
            location=(
                window_center_x, -glass_thickness / 2.0, bottom_plate_height + window_bottom_z + window_height / 2.0),
            material=glass_material
        )
        # glass_pane.parent = window_parent


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
    def create_child(parent, board_name, length, height, depth, world_location, material):
        """
        Creates a board and ensures it is correctly positioned as a child of 'parent'.

        Args:
            parent (bpy.types.Object): The parent object to attach the new child to.
            board_name (str): Name of the new object.
            length (float): Length of the board.
            height (float): Height of the board.
            depth (float): Depth of the board.
            world_location (tuple or Vector): World-space location.
            material (bpy.types.Material): Material to apply.

        Returns:
            bpy.types.Object: The newly created board object.
        """

        board = BoardFactory.add_board(
            board_name=board_name,
            length=length,
            height=height,
            depth=depth,
            location=Vector(world_location),  # Ensure it's a Vector
            material=material
        )

        board.parent = parent
        board.location = parent.matrix_world.inverted() @ Vector(world_location)  # Convert to local space

        return board

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
                    stud_size={"thickness": stud_thickness, "width": stud_width, "height": stud_thickness},
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


class HouseFactory:
    # Updated House Size (~3000 sq ft)
    HOUSE_GRID_WIDTH = 50  # 50ft wide
    HOUSE_GRID_LENGTH = 60  # 60ft long
    GRID_SIZE = 0.3048  # 1ft in meters
    HOUSE_HEIGHT = 2.7  # 2.7m (~9ft) wall height
    # Create materials
    materials = MaterialFactory.create_materials()

    # Define South-facing Windows (for Passive Solar Heating)
    SOUTH_WALL_WINDOWS = [
        {"center_x": -20 * GRID_SIZE, "bottom_z": 1, "width": 1, "height": 1.2},
        {"center_x": 0 * GRID_SIZE, "bottom_z": 0.9, "width": 1.5, "height": 2},
        {"center_x": 20 * GRID_SIZE, "bottom_z": 0.9, "width": 1.5, "height": 2}
    ]

    @staticmethod
    def create_greenhouse_wall(grid_width, glass_angle=70):
        """Creates a sloped greenhouse wall with angled glass for optimal solar gain."""

        wall_thickness = 0.5  # 6-inch thick support wall
        greenhouse_height = 12  # Total height of greenhouse side
        glass_angle_rad = math.radians(glass_angle)  # Convert angle to radians

        # **Calculate the glass wall's top position**
        glass_base_x = 0  # The base of the greenhouse glass starts at x=0
        glass_top_x = grid_width / 2  # The top leans forward toward the greenhouse
        glass_top_z = greenhouse_height  # The highest point (aligned with roof)

        # **Create the sloped glass plane**
        greenhouse_glass = WallFactory.create_framed_wall(
            name="Greenhouse_Glass",
            length=grid_width,
            height=greenhouse_height,
            location=(grid_width / 2 - 0.5, -wall_thickness / 2, greenhouse_height / 2),
            stud_spec="2x6",
            materials={"framing": None, "sheathing": None, "drywall": None, "glass": "Glass"}
        )

        # **Rotate the glass wall to 70°**
        greenhouse_glass.rotation_euler = (glass_angle_rad, 0, 0)

        return greenhouse_glass

    @staticmethod
    def create_exterior_walls():
        """
        Creates the four exterior walls with correct rotation.
        """
        walls = []
        lenght = HouseFactory.HOUSE_GRID_LENGTH * HouseFactory.GRID_SIZE
        width = HouseFactory.HOUSE_GRID_WIDTH * HouseFactory.GRID_SIZE
        height = HouseFactory.HOUSE_HEIGHT
        # West Wall (Rotated 90 degrees)
        walls.append(WallFactory.create_wall(
            name="WestWall",
            length=lenght,
            height=height,
            location=(-HouseFactory.HOUSE_GRID_WIDTH / 2 * HouseFactory.GRID_SIZE, 0, 0),
            thickness=EXTERIOR_WALL_THICKNESS,
            rotation=(0, 0, math.radians(90)),  # Rotate 90 degrees
            materials=HouseFactory.materials
        ))

        # East Wall (Rotated 90 degrees)
        walls.append(WallFactory.create_wall(
            name="EastWall",
            length=lenght,
            height=height,
            location=(HouseFactory.HOUSE_GRID_WIDTH / 2 * HouseFactory.GRID_SIZE, 0, 0),
            thickness=EXTERIOR_WALL_THICKNESS,
            rotation=(0, 0, math.radians(90)),  # Rotate 90 degrees
            materials=HouseFactory.materials
        ))

        # North Wall (No Rotation)
        walls.append(WallFactory.create_wall(
            name="NorthWall",
            length=width,
            height=height,
            location=(0, HouseFactory.HOUSE_GRID_LENGTH / 2 * HouseFactory.GRID_SIZE, 0),
            thickness=EXTERIOR_WALL_THICKNESS,
            rotation=(0, 0, 0),  # No Rotation
            materials=HouseFactory.materials
        ))

        # South Wall (No Rotation, Includes Windows)
        walls.append(WallFactory.create_wall(
            name="SouthWall",
            length=width,
            height=height,
            location=(0, -HouseFactory.HOUSE_GRID_LENGTH / 2 * HouseFactory.GRID_SIZE, 0),
            thickness=EXTERIOR_WALL_THICKNESS,
            rotation=(0, 0, 0),  # No Rotation
            materials=HouseFactory.materials,
            window_specs=HouseFactory.SOUTH_WALL_WINDOWS  # Add Windows
        ))
        # **Greenhouse (South Wall)**
        walls.append(HouseFactory.create_greenhouse_wall(HouseFactory.HOUSE_GRID_WIDTH))
        return walls

    @staticmethod
    def create_interior_walls():
        """
        Uses the 1ft x 1ft grid to determine interior wall placement.
        """
        materials = HouseFactory.materials
        walls = []
        lenght = HouseFactory.HOUSE_GRID_LENGTH * HouseFactory.GRID_SIZE
        width = HouseFactory.HOUSE_GRID_WIDTH * HouseFactory.GRID_SIZE
        height = HouseFactory.HOUSE_HEIGHT
        # Interior Wall 1 (Living Room / Kitchen Separation)
        walls.append(WallFactory.create_wall(
            name="InteriorWall1",
            length=lenght,
            height=height,
            location=(0, -10 * HouseFactory.GRID_SIZE, 0),
            thickness=INTERIOR_WALL_THICKNESS,
            rotation=(0, 0, 0),  # No Rotation
            materials=materials
        ))

        # Interior Wall 2 (Bedrooms / Hallway)
        walls.append(WallFactory.create_wall(
            name="InteriorWall2",
            length=lenght,
            height=height,
            location=(-15 * HouseFactory.GRID_SIZE, 0, 0),
            thickness=INTERIOR_WALL_THICKNESS,
            rotation=(0, 0, math.radians(90)),  # Rotate 90 degrees
            materials=materials
        ))

        # Interior Wall 3 (Bathroom Division)
        walls.append(WallFactory.create_wall(
            name="InteriorWall3",
            length=20 * HouseFactory.GRID_SIZE,
            height=height,
            location=(10 * HouseFactory.GRID_SIZE, -15 * HouseFactory.GRID_SIZE, 0),
            thickness=INTERIOR_WALL_THICKNESS,
            rotation=(0, 0, 0),  # No Rotation
            materials=materials
        ))

        return walls

    @staticmethod
    def create_room_walls(room_name, x_offset, y_offset, height=2.7):
        """
        Uses WallFactory to create walls for a given room.
        """
        length, width = ROOM_DIMENSIONS[room_name]
        wall_thickness = EXTERIOR_WALL_THICKNESS if room_name in ["living_room",
                                                                  "friends_family_room"] else INTERIOR_WALL_THICKNESS

        walls = []
        materials = HouseFactory.materials
        # Create 4 framed walls
        walls.append(WallFactory.create_framed_wall(
            name=f"{room_name}_North",
            length=length,
            height=height,
            location=(x_offset, y_offset + width / 2, 0),
            stud_thickness=wall_thickness,
            materials=materials
        ))

        walls.append(WallFactory.create_framed_wall(
            name=f"{room_name}_South",
            length=length,
            height=height,
            location=(x_offset, y_offset - width / 2, 0),
            stud_thickness=wall_thickness,
            materials=materials
        ))

        walls.append(WallFactory.create_framed_wall(
            name=f"{room_name}_East",
            length=width,
            height=height,
            location=(x_offset + length / 2, y_offset, 0),
            stud_thickness=wall_thickness,
            materials=materials
        ))

        walls.append(WallFactory.create_framed_wall(
            name=f"{room_name}_West",
            length=width,
            height=height,
            location=(x_offset - length / 2, y_offset, 0),
            stud_thickness=wall_thickness,
            materials=materials
        ))

        print(f"✅ Created walls for {room_name} at {x_offset}, {y_offset}")
        return walls

    @staticmethod
    def create_room(name, x_offset, y_offset, room_size, height=2.7, exterior=False):
        """
        Creates a room with walls and defines exterior or interior wall thickness.
        """
        wall_thickness = EXTERIOR_WALL_THICKNESS if exterior else INTERIOR_WALL_THICKNESS

        length, width = room_size
        x, y = x_offset, y_offset

        walls = []

        # Create 4 walls
        walls.append(WallFactory.create_wall(f"{name}_Wall_North", length, height, wall_thickness,
                                             (x, y + width / 2, height / 2)))
        walls.append(WallFactory.create_wall(f"{name}_Wall_South", length, height, wall_thickness,
                                             (x, y - width / 2, height / 2)))
        walls.append(WallFactory.create_wall(f"{name}_Wall_East", wall_thickness, height, width,
                                             (x + length / 2, y, height / 2)))
        walls.append(WallFactory.create_wall(f"{name}_Wall_West", wall_thickness, height, width,
                                             (x - length / 2, y, height / 2)))

        print(f"✅ Created {name} at {x}, {y}")
        return walls

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

@staticmethod
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

@staticmethod
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
def create_passive_house():
    # Constants
    EXTERIOR_WALL_THICKNESS = 0.4  # 40cm thick exterior walls
    INTERIOR_WALL_THICKNESS = 0.15  # 15cm interior walls

    """
    Generates a full passive Earthship-inspired house.
    """
    base_x, base_y = 0, 0  # Starting position
    x_offset = base_x
    y_offset = base_y

    all_walls = []

    grid_width, grid_depth = 30, 40  # Define house dimensions
    # Define room layout
    room_layout = define_room_layout(grid_width, grid_depth)

    # Create tiled floor
    # create_tiled_floor(grid_width, grid_depth, room_layout)
    """
    Constructs the full passive house.
    """
    print("🏡 Building Passive House...")

    # Step 1: Create Exterior Walls
    exterior_walls = HouseFactory.create_exterior_walls()

    print("✅ Exterior Walls Created")

    # Step 2: Create Interior Walls
    interior_walls = HouseFactory.create_interior_walls()

    print("✅ Interior Walls Created")

    print("🏡 Passive House Construction Completed!")

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


if __name__ == "__main__":
    # demo_wall_test()
    create_passive_house()
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