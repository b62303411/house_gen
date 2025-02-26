# door_factory.py
import importlib

import bpy
from mathutils import Vector

import frame_factory
from board_factory import BoardFactory
importlib.reload(frame_factory)
from frame_factory import FramingFactory
class DoorFactory:

    @staticmethod
    def create_single_door(parent, name_prefix, width, height, thickness, materials):
        frame_material = materials['framing']
        glass_material = materials['glass']
        """Creates a single door."""
        door = BoardFactory.add_board(
            parent=parent,
            board_name=f"{name_prefix}_SingleDoor",
            length=width,
            height=height,
            depth=thickness,
            location=(0, 0, height/2),
            material=frame_material
        )
        return door


    @staticmethod
    def create_patio_door(parent, name_prefix, width, height, thickness, materials):
        """Creates a two-panel sliding patio door with overlapping sliding panels on rails."""
        panel_width = width / 2
        frame_thickness = 0.05
        glass_thickness = 0.01
        rail_offset = 0.02  # Offset to simulate sliding mechanism

        frame_material = materials['framing']
        glass_material = materials['glass']

        def create_frame_and_glass(offset_x, side, z_offset):
            top_frame = BoardFactory.add_board(
                parent=parent,
                board_name=f"{name_prefix}_Patio{side}TopFrame",
                length=panel_width,
                height=frame_thickness,
                depth=thickness,
                location=(offset_x, z_offset, height - (frame_thickness / 2)),
                material=frame_material
            )
            bottom_frame = BoardFactory.add_board(
                parent=parent,
                board_name=f"{name_prefix}_Patio{side}BottomFrame",
                length=panel_width,
                height=frame_thickness,
                depth=thickness,
                location=(offset_x, z_offset, frame_thickness / 2),
                material=frame_material
            )
            left_frame = BoardFactory.add_board(
                parent=parent,
                board_name=f"{name_prefix}_Patio{side}LeftFrame",
                length=frame_thickness,
                height=height,
                depth=thickness,
                location=(offset_x - (panel_width / 2), z_offset, height / 2),
                material=frame_material
            )
            right_frame = BoardFactory.add_board(
                parent=parent,
                board_name=f"{name_prefix}_Patio{side}RightFrame",
                length=frame_thickness,
                height=height,
                depth=thickness,
                location=(offset_x + (panel_width / 2), z_offset, height / 2),
                material=frame_material
            )
            glass_panel = BoardFactory.add_board(
                parent=parent,
                board_name=f"{name_prefix}_Patio{side}Glass",
                length=panel_width - 0.1,
                height=height - 0.1,
                depth=glass_thickness,
                location=(offset_x, z_offset, height / 2),
                material=glass_material
            )
            return top_frame, bottom_frame, left_frame, right_frame, glass_panel

        left_door = create_frame_and_glass(-panel_width / 2, "Left", -rail_offset)
        right_door = create_frame_and_glass(panel_width / 2, "Right", rail_offset)

    @staticmethod
    def create_double_door(parent, name_prefix, width, height, thickness, materials):
        """Creates a double swinging door."""
        frame_material = materials['framing']
        glass_material = materials['glass']
        panel_width = width / 2
        left_door = BoardFactory.add_board(
            parent=parent,
            board_name=f"{name_prefix}_DoubleLeft",
            length=panel_width,
            height=height,
            depth=thickness,
            location=(-panel_width / 2, 0, 0),
            material=frame_material
        )
        right_door = BoardFactory.add_board(
            parent=parent,
            board_name=f"{name_prefix}_DoubleRight",
            length=panel_width,
            height=height,
            depth=thickness,
            location=(panel_width / 2, 0, 0),
            material=frame_material
        )
        return left_door, right_door

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
        materials=None,
        is_load_bearing=False,
        door_type="single"
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
        frame_mat = materials["framing"]
        glass_mat = materials["glass"]
        # 1) Create an Empty to parent all door parts
        bpy.ops.object.empty_add(type='PLAIN_AXES')
        door_parent = bpy.context.object
        door_parent.name = f"{wall.name}_Door"
        door_parent.parent = wall
        door_parent.location = (door_center_x, 0, 0)

        header_spec = FramingFactory.create_header_spec(
                opening_width=door_width,
                bottom_plate_height=bottom_plate_height,
                opening_bottom_z=door_bottom_z,
                opening_height=door_height,
                wall_height=wall_height,
                top_plate_height=top_plate_height,
                second_top_plate_height=second_top_plate_height,
                stud_spec=stud_spec,
                is_load_bearing=True)

        # 2) Cut opening
        cut_ok = FramingFactory.cut_opening(
            opening_parent=door_parent,
            wall_structure=wall,
            name_prefix=name_prefix,
            bottom_z=door_bottom_z,
            opening_width=door_width,
            opening_height=door_height-header_spec["header_height"],
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
            material=frame_mat,
            parent=door_parent
        )

        # 4) If load-bearing, create header & jack studs
        if is_load_bearing:
            header,header_z_center,header_height= FramingFactory.create_header(
                name_prefix=name_prefix,
                header_spec=header_spec,
                material=frame_mat,
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
                material=frame_mat
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
                material=frame_mat
            )
            print(f"✅ Created door threshold: {threshold_obj.name}")

        print("✅ Door framing creation complete.")

        if door_type == "single":
            DoorFactory.create_single_door(door_parent, name_prefix, door_width, door_height-.1, thickness, materials)
        elif door_type == "patio":
            DoorFactory.create_patio_door(door_parent, name_prefix, door_width, header_z_center-header_height/2, thickness, materials)
        elif door_type == "double":
            DoorFactory.create_double_door(door_parent, name_prefix, door_width, door_height, thickness, materials)
        else:
            print(f"❌ Unsupported door type: {door_type}")
            return None

        return door_parent
