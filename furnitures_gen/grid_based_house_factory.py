import math

from house_factory import HouseFactory
from walls import WallFactory, INTERIOR_WALL_THICKNESS, EXTERIOR_WALL_THICKNESS


class GridBasedHouseFactory:
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