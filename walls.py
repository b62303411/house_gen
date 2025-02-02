import bpy
import math

# -------------------------------------------------------------------
# MATERIALS (simple placeholders)
# -------------------------------------------------------------------
class MaterialFactory:
    def create_wood_material(name="FramingWood"):
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (0.8, 0.6, 0.4, 1.0)
            bsdf.inputs["Roughness"].default_value = 0.5
        return mat

    def create_sheathing_material(name="SheathingOSB"):
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (0.7, 0.6, 0.4, 1.0)
            bsdf.inputs["Roughness"].default_value = 0.7
        return mat

    def create_drywall_material(name="Drywall"):
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (0.9, 0.9, 0.9, 1.0)
            bsdf.inputs["Roughness"].default_value = 0.8
        return mat
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

        # Principled BSDF
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
            bsdf.inputs["Base Color"].default_value = (0.8, 0.9, 1, 0.5)
            bsdf.inputs["Transmission"].default_value = 1.0
            bsdf.inputs["Roughness"].default_value = 0.1
            bsdf.inputs["IOR"].default_value = 1.45

        return material

# -------------------------------------------------------------------
# CONSTANTS/DEFAULTS
# -------------------------------------------------------------------

# Typical 2×4 approximation in meters:
STUD_THICKNESS = 0.0381  # 1.5 inches
STUD_WIDTH     = 0.0889  # 3.5 inches
STUD_SPACING   = 0.4064  # ~16 inches on center



# -------------------------------------------------------------------
# UTILITY: Move object to a specific collection
# -------------------------------------------------------------------

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
    def add_cladding(wall_name, cladding_type, wall_length, wall_height, thickness, y_offset, material, location,
                     wall_coll, sheet_length, sheet_height):
        # Calculate number of sheets needed in length and height directions
        num_length_sheets = int(wall_length // sheet_length)
        remaining_length = wall_length % sheet_length
        num_height_sheets = int(wall_height // sheet_height)
        remaining_height = wall_height % sheet_height

        # Wall's origin coordinates (bottom-left corner)
        start_x = location[0] - wall_length / 2
        start_z = location[2]

        # Create sheets in grid pattern
        for col in range(num_length_sheets + 1):
            for row in range(num_height_sheets + 1):
                # Determine current sheet dimensions
                cladding_length = sheet_length if col < num_length_sheets else remaining_length
                cladding_height = sheet_height if row < num_height_sheets else remaining_height

                # Skip if no remaining space
                if cladding_length <= 0 or cladding_height <= 0:
                    continue

                # Calculate sheet position (center coordinates)
                pos_x = start_x + (col * sheet_length) + cladding_length / 2
                pos_z = start_z + (row * sheet_height) + cladding_height / 2
                pos_y = y_offset  # Already calculated offset from wall center

                sheet_obj = BoardFactory.add_board(
                    board_name=f"{wall_name}_{cladding_type}_{col}_{row}",
                    length=cladding_length,
                    height=cladding_height,
                    depth=thickness,
                    location=(pos_x, pos_y, pos_z),
                    material=material
                )
                move_to_collection(sheet_obj, wall_coll)
    def add_board(board_name, length, height, depth, location, material=None):
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
        obj.scale = (length/2.0, depth/2.0, height/2.0)
        bpy.ops.object.transform_apply(scale=True)

        if material:
            obj.data.materials.append(material)

        return obj

# -------------------------------------------------------------------
# OPTIONAL WINDOW CREATION: Header, sill, jack studs
# -------------------------------------------------------------------
class WindowFactory:
    def create_window_opening(
        wall_coll,
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
        material=None
    ):
        """
        Creates a minimal window framing: a header, sill, and left/right jack studs
        within the total 'wall_height'.
        """
        # For simplicity, we'll assume one 2×4 thick header (on edge).
        header_thickness = stud_size["height"]  # ~0.0381
        header_width     = stud_size["width"]   # ~0.0889

        # The top of the window opening is at (window_bottom_z + window_height).
        # We'll place the header's bottom at that point, or clamp if near top plates.
        header_z = bottom_plate_height + window_bottom_z + window_height
        max_header_z = wall_height - (top_plate_height + second_top_plate_height + header_thickness)
        if header_z > max_header_z:
            header_z = max_header_z

        header = BoardFactory.add_board(
            board_name=f"{name_prefix}_Header",
            length=window_width + stud_size["thickness"]*2,
            height=header_thickness,
            depth=header_width,
            location=(window_center_x, 0, header_z + header_thickness/2.0),
            material=material
        )
        move_to_collection(header, wall_coll)

        # Sill: place a horizontal 2×4 at the bottom of the window
        sill_thickness = stud_size["height"]
        sill_z = bottom_plate_height + window_bottom_z - sill_thickness
        if sill_z > bottom_plate_height:
            sill = BoardFactory.add_board(
                board_name=f"{name_prefix}_Sill",
                length=window_width + stud_size["thickness"]*2,
                height=sill_thickness,
                depth=stud_size["width"],
                location=(window_center_x, 0, sill_z + sill_thickness/2.0),
                material=material
            )
            move_to_collection(sill, wall_coll)

        # Jack studs
        jack_height = header_z - bottom_plate_height
        if jack_height > 0:
            left_x = window_center_x - (window_width/2.0) - (stud_size["thickness"]/2.0)
            right_x= window_center_x + (window_width/2.0) + (stud_size["thickness"]/2.0)

            lj = BoardFactory.add_board(
                board_name=f"{name_prefix}_JackStudLeft",
                length=stud_size["thickness"],
                height=jack_height,
                depth=stud_size["width"],
                location=(left_x, 0, bottom_plate_height + jack_height/2.0),
                material=material
            )
            move_to_collection(lj, wall_coll)

            rj = BoardFactory.add_board(
                board_name=f"{name_prefix}_JackStudRight",
                length=stud_size["thickness"],
                height=jack_height,
                depth=stud_size["width"],
                location=(right_x, 0, bottom_plate_height + jack_height/2.0),
                material=material
            )
            move_to_collection(rj, wall_coll)

# -------------------------------------------------------------------
# CREATE FRAMED WALL with Sheathing (exterior) & Drywall (interior)
# -------------------------------------------------------------------
class WallFactory:
    def create_framed_wall(
        name,
        length,
        height,       # total wall height, including bottom + top plates
        location=(0,0,0),
        stud_spacing=STUD_SPACING,
        stud_thickness=STUD_THICKNESS,
        stud_width=STUD_WIDTH,
        bottom_plate_count=1,
        top_plate_count=2,
        add_sheathing=True,
        add_drywall=True,
        window_specs=None,
        materials=None
    ):
        material_framing=materials['framing']
        material_sheathing=materials['sheathing']
        material_drywall=materials['drywall']
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
        # Create a new collection
        wall_coll = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(wall_coll)

        # 1) BOTTOM PLATES
        plate_thickness = stud_thickness
        plate_depth     = stud_width

        total_bottom_height = plate_thickness * bottom_plate_count
        for i in range(bottom_plate_count):
            z_plate = location[2] + plate_thickness/2.0 + i*plate_thickness
            plate = BoardFactory.add_board(
                board_name=f"{name}_BottomPlate_{i+1}",
                length=length,
                height=plate_thickness,
                depth=plate_depth,
                location=(location[0], location[1], z_plate),
                material=material_framing
            )
            move_to_collection(plate, wall_coll)

        # 2) TOP PLATES
        total_top_height = plate_thickness * top_plate_count
        z_top_start = location[2] + height - total_top_height
        for i in range(top_plate_count):
            z_plate = z_top_start + plate_thickness/2.0 + i*plate_thickness
            plate = BoardFactory.add_board(
                board_name=f"{name}_TopPlate_{i+1}",
                length=length,
                height=plate_thickness,
                depth=plate_depth,
                location=(location[0], location[1], z_plate),
                material=material_framing
            )
            move_to_collection(plate, wall_coll)

        # 3) STUD REGION
        # The "net" region for studs is from top of bottom plates to bottom of top plates.
        stud_region_height = height - (total_bottom_height + total_top_height)
        if stud_region_height < 0:
            stud_region_height = 0
        z_stud_bottom = location[2] + total_bottom_height

        # Place studs along X at 'stud_spacing' intervals
        x_left = location[0] - (length/2.0) + (stud_thickness/2.0)
        n_studs = int((length - stud_thickness) // stud_spacing) + 1

        for i in range(n_studs):
            x_i = x_left + i * stud_spacing
            if x_i + stud_thickness/2.0 > (location[0] + length/2.0):
                break
            z_center = z_stud_bottom + stud_region_height/2.0
            stud_obj = BoardFactory.add_board(
                board_name=f"{name}_Stud_{i+1}",
                length=stud_thickness,
                height=stud_region_height,
                depth=stud_width,
                location=(x_i, location[1], z_center),
                material=material_framing
            )
            move_to_collection(stud_obj, wall_coll)

        # 4) WINDOW FRAMING (optional)
        if window_specs:
            WindowFactory.create_window_opening(
                wall_coll=wall_coll,
                name_prefix=f"{name}_Window",
                window_center_x=window_specs["center_x"],
                window_bottom_z=window_specs["bottom_z"],
                window_width=window_specs["width"],
                window_height=window_specs["height"],
                bottom_plate_height=total_bottom_height,
                top_plate_height=plate_thickness,
                stud_size={"thickness": stud_thickness, "width": stud_width, "height": stud_thickness},
                wall_height=height,
                second_top_plate_height=plate_thickness if top_plate_count>1 else 0,
                material=material_framing
            )

        # 5) Exterior Sheathing
        if add_sheathing:
            sheathing_thickness = 0.012  # ~12 mm
            # Sheathing goes on the "outside" (we'll treat negative Y as outside)
            sheathing_y = location[1] - (plate_depth / 2.0 + sheathing_thickness / 2.0)

            BoardFactory.add_cladding(
                wall_name=name,
                cladding_type="Sheathing",
                wall_length=length,
                wall_height=height,
                thickness=sheathing_thickness,
                y_offset=sheathing_y,
                material=material_sheathing,
                location=location,
                wall_coll=wall_coll,
                sheet_length=2.44,  # Standard 8ft sheet
                sheet_height=1.22  # Standard 4ft sheet
            )


            sheathing_z = location[2] + height/2.0
            #sheathing_obj = BoardFactory.add_board(
            #    board_name=f"{name}_Sheathing",
            #    length=length,
            #    height=height,
            #    depth=sheathing_thickness,
            #    location=(location[0], sheathing_y, sheathing_z),
            #    material=material_sheathing
            #)
            #move_to_collection(sheathing_obj, wall_coll)

        # 6) Interior Drywall
        if add_drywall:
            drywall_thickness = 0.0127  # 1/2 inch ~ 0.0127 m
            # We'll treat +Y as inside, so place drywall behind studs
            drywall_y = location[1] + (plate_depth/2.0 + drywall_thickness/2.0)
            drywall_z = location[2] + height/2.0
            drywall_obj = BoardFactory.add_board(
                board_name=f"{name}_Drywall",
                length=length,
                height=height,
                depth=drywall_thickness,
                location=(location[0], drywall_y, drywall_z),
                material=material_drywall
            )
            move_to_collection(drywall_obj, wall_coll)

        return wall_coll

# -------------------------------------------------------------------
# TEST / DEMO
# -------------------------------------------------------------------

def demo_wall_test():
    """
    Demonstrates creating one wall with:
      - Correct stud length
      - Sheathing
      - Drywall
      - An optional window
    Then places a camera & sun so you can see it.
    """

    # Clear scene
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    # Create materials
    mat_framing   = MaterialFactory.create_wood_material("FramingWood")
    mat_sheathing = MaterialFactory.create_sheathing_material("SheathingOSB")
    mat_drywall   = MaterialFactory.create_drywall_material("Drywall")
    materials = {}
    materials['framing']=mat_framing
    materials['sheathing']=mat_sheathing
    materials['drywall']=mat_drywall
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

    # Create the framed wall
    wall_coll = WallFactory.create_framed_wall(
        name="TestWall",
        length=wall_length,
        height=wall_height,
        location=(0,0,0),
        stud_spacing=STUD_SPACING,
        stud_thickness=STUD_THICKNESS,
        stud_width=STUD_WIDTH,
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

if __name__ == "__main__":
    demo_wall_test()