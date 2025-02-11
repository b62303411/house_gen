import importlib

import bpy
import math

import furniture_factory
from board_factory import BoardFactory
from door_factory import DoorFactory
from furniture_factory import FurnitureFactory
from materials import MaterialFactory
from walls import WallFactory, EXTERIOR_WALL_THICKNESS, INTERIOR_WALL_THICKNESS, ROOM_DIMENSIONS, define_room_layout
from windows import WindowFactory
from math import radians
from mathutils import Euler
importlib.reload(furniture_factory)
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
        {"center_x": -20 * GRID_SIZE, "bottom_z": 0.5, "width": 1.5, "height": 2},
        {"center_x": 0 * GRID_SIZE, "bottom_z": 0.5, "width": 1.5, "height": 2},
        {"center_x": 20 * GRID_SIZE, "bottom_z": 0.5, "width": 1.5, "height": 2}
    ]

    @staticmethod
    def create_prototypes():
        FurnitureFactory.create_furniture_prototypes()

    @staticmethod
    def create_furniture():
        FurnitureFactory.create_furniture_prototypes()
        FurnitureFactory.place_furniture()

    @staticmethod
    def create_wall_segment(
            parent,
            start_xy,
            end_xy,
            wall_height,
            stud_spacing,
            materials,
            segment_name,
            stud_type="2x6",
            window_specs=None
    ):
        """
        Creates an exterior wall segment with:
          - 2×6 studs,
          - 1 bottom plate (flush to segment length),
          - 2 top plates:
              * First top plate flush
              * Second top plate extends by overlap_start + overlap_end
                to tie into adjacent walls.
          - Regular studs at 'stud_spacing', skipping corners.
          - No corner studs (those are placed by place_corner_assembly).

        parent:       the Empty to which this segment is parented.
        start_xy:     (x0, y0) world coords for segment start.
        end_xy:       (x1, y1) world coords for segment end.
        wall_height:  total height from floor to top of the second top plate.
        stud_spacing: spacing for vertical studs (e.g., ~0.4064 for 16" o.c.).
        materials:    dictionary with 'framing', etc.
        segment_name: string name for the segment.
        overlap_start, overlap_end: how much the 2nd top plate extends
                                    beyond the nominal segment at each side.
        """
        # 1) Compute segment geometry
        x0, y0 = start_xy
        x1, y1 = end_xy
        dx = x1 - x0
        dy = y1 - y0
        seg_length = math.hypot(dx, dy)

        mx = (x0 + x1) * 0.5
        my = (y0 + y1) * 0.5
        angle_z = math.atan2(dy, dx)

        # 2) Create a parent Empty
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=(mx, my, 0))
        segment_parent = bpy.context.object
        segment_parent.name = segment_name
        segment_parent.parent = parent
        segment_parent.rotation_euler[2] = angle_z
        spec = WallFactory.STUD_SPECS[stud_type]
        # 3) Dimensions & material
        stud_t = spec["thickness"]  # ~0.0381 m (1.5")
        stud_w = spec["width"]  # ~0.1397 m (5.5")
        mat_framing = materials.get("framing")
        material_sheathing = materials.get("sheathing")
        mat_glass = materials.get("glass")
        plate_thickness = stud_t
        plate_depth = stud_w
        bottom_plate_count = 1
        top_plate_count = 2
        x_shift = stud_w / 2
        # === Bottom Plate (flush) ===
        bpy.ops.object.select_all(action='DESELECT')
        bottom_plate = BoardFactory.add_board(
            parent=segment_parent,
            board_name=f"{segment_name}_BottomPlate",
            length=seg_length,
            height=plate_thickness,
            depth=plate_depth,
            location=(-x_shift, 0, plate_thickness * 0.5),
            material=mat_framing
        )

        # === First Top Plate (flush) ===
        # Placed just below the second top plate
        first_top_plate_z = wall_height - (plate_thickness * 1.5)
        first_top_plate = BoardFactory.add_board(
            parent=segment_parent,
            board_name=f"{segment_name}_TopPlate_1",
            length=seg_length,
            height=plate_thickness,
            depth=plate_depth,
            location=(-x_shift, 0, first_top_plate_z),
            material=mat_framing
        )

        # === Second Top Plate (with overlap) ===

        # shift in local X so overlap_start extends behind the segment start, overlap_end extends forward

        second_top_plate_z = wall_height - (plate_thickness * 0.5)
        second_top_plate = BoardFactory.add_board(
            parent=segment_parent,
            board_name=f"{segment_name}_TopPlate_2",
            length=seg_length,
            height=plate_thickness,
            depth=plate_depth,
            location=(x_shift, 0, second_top_plate_z),
            material=mat_framing
        )

        # === Stud region ===
        total_plates_thickness = plate_thickness * (bottom_plate_count + top_plate_count)
        net_stud_height = wall_height - total_plates_thickness
        if net_stud_height < 0:
            net_stud_height = 0

        # We'll skip corner studs => margin
        margin = plate_thickness
        x_left = -(seg_length * 0.5) + margin
        x_right = (seg_length * 0.5) - margin

        stud_z_bottom = plate_thickness * bottom_plate_count
        stud_center_z = stud_z_bottom + (net_stud_height * 0.5)

        # Place regular studs
        x_i = x_left
        stud_index = 1
        corner_offset = x_right - stud_w * 2
        while x_i <= corner_offset + 0.0001:
            if x_i > x_right:
                x_i = x_right

            BoardFactory.add_board(
                parent=segment_parent,
                board_name=f"{segment_name}_Stud_{stud_index}",
                length=plate_thickness,  # along local X
                height=net_stud_height,  # along local Z
                depth=plate_depth,  # along local Y
                location=(x_i + stud_w * 2, 0, stud_center_z),
                material=mat_framing
            )
            x_i += stud_spacing
            stud_index += 1

        offset_corner = stud_w / 2 - stud_t / 2
        seg_start = seg_length / 2
        # corner 1
        BoardFactory.add_board(
            parent=segment_parent,
            board_name=f"{segment_name}_Stud_corner1",
            length=plate_thickness,  # along local X
            height=net_stud_height,  # along local Z
            depth=plate_depth,  # along local Y
            location=(-(seg_start + offset_corner), 0, stud_center_z),
            material=mat_framing
        )

        rotation_degrees = (0, 0, 90)
        rotation_radians = [radians(angle) for angle in rotation_degrees]

        # corner 2
        BoardFactory.add_board(
            parent=segment_parent,
            board_name=f"{segment_name}_Stud_corner2",
            length=plate_thickness,  # along local X
            height=net_stud_height,  # along local Z
            depth=plate_depth,  # along local Y
            location=(-(seg_start) + stud_t, offset_corner, stud_center_z),
            material=mat_framing,
            rotation=rotation_radians
        )
        # corner 3
        BoardFactory.add_board(
            parent=segment_parent,
            board_name=f"{segment_name}_Stud_corner3",
            length=plate_thickness,  # along local X
            height=net_stud_height,  # along local Z
            depth=plate_depth,  # along local Y
            location=(-(seg_start) + stud_t, -offset_corner, stud_center_z),
            material=mat_framing,
            rotation=rotation_radians
        )

        # corner 4
        BoardFactory.add_board(
            parent=segment_parent,
            board_name=f"{segment_name}_Stud_corner4",
            length=plate_thickness,  # along local X
            height=net_stud_height,  # along local Z
            depth=plate_depth,  # along local Y
            location=(((seg_length / 2) - (x_shift + stud_t / 2)), 0, stud_center_z),
            material=mat_framing
        )

        add_sheathing = True
        # 5) Exterior Sheathing
        if add_sheathing:
            sheathing_thickness = 0.012  # ~12 mm
            # Sheathing goes on the "outside" (we'll treat negative Y as outside)
            sheathing_y = - (plate_depth / 2.0 + sheathing_thickness / 2.0)

            BoardFactory.add_cladding(
                wall_name=segment_name,
                cladding_type="Sheathing",
                wall_length=seg_length,
                wall_height=wall_height,
                thickness=sheathing_thickness,
                y_offset=sheathing_y,
                material=material_sheathing,
                location=(0, 0, 0),
                wall=segment_parent,
                sheet_length=2.44,  # Standard 8ft sheet
                sheet_height=1.22  # Standard 4ft sheet
            )

            sheathing_z = wall_height / 2.0

        # 4) WINDOW FRAMING (optional)
        if window_specs:
            for ws in window_specs:
                WindowFactory.create_window_opening(
                    wall=segment_parent,
                    name_prefix=f"{segment_name}_Window",
                    window_center_x=ws["center_x"],
                    window_bottom_z=ws["bottom_z"],
                    window_width=ws["width"],
                    window_height=ws["height"],
                    bottom_plate_height=0,
                    top_plate_height=plate_thickness,
                    stud_spec=spec,
                    wall_height=wall_height,
                    second_top_plate_height=plate_thickness if top_plate_count > 1 else 0,
                    material=mat_framing,
                    glass_material=mat_glass
                )
        # Create a door
        DoorFactory.create_door_opening(
            wall=segment_parent,
            name_prefix="MyDoor",
            door_center_x=6.0,
            door_bottom_z=0.0,
            door_width=0.91,
            door_height=2.03,
            bottom_plate_height=0.0381,
            top_plate_height=0.0381,
            stud_spec=spec,
            wall_height=2.7432,
            second_top_plate_height=0.0381,
            material=None,
            is_load_bearing=True
        )
        return segment_parent

    @staticmethod
    def create_outer_wall(name, footprint_points, wall_height, stud_spacing, materials, windows_spec):
        """
        Construit un mur externe formé de plusieurs segments (une boucle).
        Chaque paire consécutive de points (i -> i+1) définit un mur droit.
        Ensuite, on place un assemblage de coin (4 montants) à chaque sommet.
        """
        # 1) Créer l'objet parent principal
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
        outer_wall_parent = bpy.context.object
        outer_wall_parent.name = name

        # Create a plane mesh
        bpy.ops.mesh.primitive_plane_add(size=2, enter_editmode=False, align='WORLD', location=(0, 0, 0))

        num_points = len(footprint_points)

        # 2) Construire chaque segment de mur
        for i in range(num_points):
            x0, y0 = footprint_points[i]
            x1, y1 = footprint_points[(i + 1) % num_points]  # point suivant (boucle)
            # Example logic: let even segments overlap by 0.2 m at the 'end',
            # odd segments overlap by 0.2 m at the 'start'.
            # (In reality, decide interior vs. exterior corners or whichever logic you want.)
            window_spec = windows_spec[i]
            # Appel à create_wall_segment(...)
            # => construit le segment entre (x0, y0) et (x1, y1)
            HouseFactory.create_wall_segment(
                parent=outer_wall_parent,
                start_xy=(x0, y0),
                end_xy=(x1, y1),
                wall_height=wall_height,
                stud_spacing=stud_spacing,
                materials=materials,
                segment_name=f"{name}_Segment_{i + 1}",
                window_specs=window_spec
            )

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