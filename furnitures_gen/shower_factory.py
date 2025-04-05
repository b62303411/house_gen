# shower_factory.py
import bpy
from furnitures_gen.board_factory import BoardFactory
from materials import MaterialFactory


class ShowerFactory:

    @staticmethod
    def create_corner_shower(name='shower',parent=None,  width=1.2, depth=1.2, height=1.5, glass_thickness=.01, base_thickness=.1, materials=None):
        bpy.ops.object.empty_add(type='PLAIN_AXES')
        parent = bpy.context.object
        parent.name = name
        materials = MaterialFactory.create_materials()

        """Creates a corner glass shower with a waterproof base and a centered drain."""
        glass_material = materials['glass']
        door_material = materials.get('door', glass_material)  # Use different material for door if specified
        base_material = materials['ceramic']  # Base should be waterproof material like ceramic or acrylic

        # Offsets for positioning
        wall_offset_x = width / 2
        wall_offset_y = depth / 2
        door_offset_x = wall_offset_x / 2  # Centered door

        # **Glass Panels** forming the corner (Left & Right Walls)
        left_glass_wall = BoardFactory.add_board(
            parent=parent,
            board_name=f"{name}_LeftGlassWall",
            length=glass_thickness,
            height=height,
            depth=depth,
            location=(-wall_offset_x, 0, height / 2),
            material=glass_material
        )
        right_glass_wall = BoardFactory.add_board(
            parent=parent,
            board_name=f"{name}_RightGlassWall",
            length=width,
            height=height,
            depth=glass_thickness,
            location=(0, wall_offset_y, height / 2),
            material=glass_material
        )

        # **Glass Door** (centered)
        door_width = width / 2
        door = BoardFactory.add_board(
            parent=parent,
            board_name=f"{name}_GlassDoor",
            length=door_width,
            height=height - 0.05,  # Slightly shorter than the walls
            depth=glass_thickness,
            location=(door_offset_x, wall_offset_y, height / 2),
            material=door_material
        )

        # **Shower Base**
        base = BoardFactory.add_board(
            parent=parent,
            board_name=f"{name}_ShowerBase",
            length=width,
            height=base_thickness,
            depth=depth,
            location=(0, 0, base_thickness / 2),
            material=base_material
        )

        # **Drain (small circular cutout)**
        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.05,  # Drain size ~10cm diameter
            depth=base_thickness / 2,  # Embedded in base
            location=(0, 0, base_thickness)  # Centered on base
        )
        drain = bpy.context.object
        drain.name = f"{name}_Drain"
        drain.parent = parent

        print("✅ Created corner shower enclosure with base and drain.")
        return parent
