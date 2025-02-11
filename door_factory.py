# door_factory.py
import bpy
from mathutils import Vector
from board_factory import BoardFactory
from frame_factory import FramingFactory

class DoorFactory:
    @staticmethod
    def create_door_opening(
        wall,
        name_prefix,
        door_center_x,
        door_bottom_z,
        door_width,
        door_height,
        bottom_plate_height,
        top_plate_height,
        stud_spec,
        wall_height,
        second_top_plate_height=0.0381,
        material=None,
        is_load_bearing=False
    ):
        """
        High-level method for creating a door opening with minimal door framing:
         1) Cut the opening.
         2) Create king studs.
         3) (Optional) Create header (if load-bearing).
         4) Create jack studs (if load-bearing).
         5) Add a threshold board, if desired.
        """
        thickness = stud_spec["thickness"]
        depth = stud_spec["width"]

        # 1) Create an Empty to parent all door parts
        bpy.ops.object.empty_add(type='PLAIN_AXES')
        door_parent = bpy.context.object
        door_parent.name = f"{wall.name}_Door"
        door_parent.parent = wall
        door_parent.location = (door_center_x, 0, 0)

        # 2) Cut opening
        cut_ok = FramingFactory.cut_opening(
            opening_parent=door_parent,
            wall_structure=wall,
            name_prefix=name_prefix,
            bottom_z=door_bottom_z,
            opening_width=door_width,
            opening_height=door_height,
            bottom_plate_height=bottom_plate_height,
            stud_spec=stud_spec
        )
        if not cut_ok:
            print("❌ Failed to cut door opening. Aborting.")
            return None

        # 3) King studs on each side
        FramingFactory.create_king_studs(
            name_prefix=name_prefix,
            opening_width=door_width,
            bottom_plate_height=bottom_plate_height,
            top_plate_height=top_plate_height,
            second_top_plate_height=second_top_plate_height,
            stud_spec=stud_spec,
            wall_height=wall_height,
            material=material,
            parent=door_parent
        )

        # 4) If load-bearing, create header & jack studs
        if is_load_bearing:
            FramingFactory.create_header(
                name_prefix=name_prefix,
                opening_width=door_width,
                bottom_plate_height=bottom_plate_height,
                opening_bottom_z=door_bottom_z,
                opening_height=door_height,
                wall_height=wall_height,
                top_plate_height=top_plate_height,
                second_top_plate_height=second_top_plate_height,
                stud_spec=stud_spec,
                is_load_bearing=True,
                material=material,
                parent=door_parent
            )
            FramingFactory.create_jack_studs(
                name_prefix=name_prefix,
                opening_width=door_width,
                bottom_plate_height=bottom_plate_height,
                opening_bottom_z=door_bottom_z,
                opening_height=door_height,
                stud_spec=stud_spec,
                parent=door_parent,
                material=material
            )

        # 5) Add threshold (optional)
        #    Example: 1" tall threshold board at bottom of door
        threshold_height = 0.0254  # ~1 inch
        threshold_z = bottom_plate_height + door_bottom_z - threshold_height
        if threshold_z >= bottom_plate_height:
            threshold_obj = BoardFactory.add_board(
                parent=door_parent,
                board_name=f"{name_prefix}_Threshold",
                length=door_width,
                height=threshold_height,
                depth=depth,
                location=(0, 0, threshold_z + threshold_height / 2.0),
                material=material
            )
            print(f"✅ Created door threshold: {threshold_obj.name}")

        print("✅ Door framing creation complete.")
        return door_parent
