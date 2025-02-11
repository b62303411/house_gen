import bpy
from materials import MaterialFactory
from board_factory import BoardFactory
from walls import WallFactory
from windows import WindowFactory
from mathutils import Vector
from math import radians
from mathutils import Euler
import math
class SegmentFactory:
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
        return segment_parent