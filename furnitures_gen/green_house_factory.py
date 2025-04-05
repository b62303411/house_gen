import bpy

from floor_plan_reader import math
from house_factory import HouseFactory
from walls import ROOM_DIMENSIONS, EXTERIOR_WALL_THICKNESS, INTERIOR_WALL_THICKNESS, WallFactory, define_room_layout


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