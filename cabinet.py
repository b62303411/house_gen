import bpy
import math
from mathutils import Vector


# ==========================
# Utility: Create a Board
# ==========================
def create_board(name, width, height, thickness, location=(0, 0, 0), rotation=(0, 0, 0), parent=None, material=None):
    """
    Creates a rectangular board (like a single panel or stretcher) as a mesh object,
    with its center at 'location'.

    - width  -> dimension along local X
    - height -> dimension along local Y
    - thickness -> dimension along local Z
    """
    bpy.ops.mesh.primitive_cube_add(size=1, location=location, rotation=rotation)
    board_obj = bpy.context.object
    board_obj.name = name
    # Scale to match the requested board dimensions
    board_obj.scale = (width / 2, height / 2, thickness / 2)
    if parent:
        board_obj.parent = parent
    if material:
        mat = bpy.data.materials.get(material)
        if mat is not None:
            if len(board_obj.data.materials) < 1:
                board_obj.data.materials.append(mat)
            else:
                board_obj.data.materials[0] = mat
    return board_obj


# ==========================
# Main CabinetFactory Class
# ==========================
class CabinetFactory:

    @staticmethod
    def create_cabinet(
            name_prefix, location=(0, 0, 0),
            cabinet_width=0.9, cabinet_height=0.9, cabinet_depth=0.6,
            is_face_frame=True,  # True = face-frame style, False = frameless
            toe_kick_height=0.1143,  # ~4.5 inches
            toe_kick_depth=0.0762,  # ~3 inches
            add_countertop=True,
            countertop_thickness=0.038,  # ~1.5"
            # Panels
            carcass_thickness=0.019,  # ~3/4" (typical plywood)
            back_thickness=0.00635,  # ~1/4"
            door_frame_thickness=0.019,  # ~3/4" for door stiles/rails
            door_panel_thickness=0.0127,  # ~1/2" door panel
            # Face Frame
            face_frame_width=0.038,  # ~1.5" typical face-frame stiles/rails
            # Shelves / Drawers / Doors
            shelf_count=1,
            drawer_count=1,
            door_count=1,
            # Materials
            material_carcass="CarcassMaterial",
            material_faceframe="FrameMaterial",
            material_counter="CountertopMaterial",
            material_door="DoorMaterial",
    ):
        """
        Creates a cabinet with separate panels (sides, bottom, back, stretchers, toe-kick).
        For face-frame style, adds a front frame. Also can add shelves, drawers, and doors.

        Realistic approach following MWA Woodworks:
        - Panel-based carcass
        - Toe-kick notch & board
        - Stretchers at top (and optional middle divider)
        - Face-frame or frameless
        - Doors and drawers with five-piece door/drawer fronts
        - Shelves (adjustable or fixed)
        - Optional countertop

        All dimension units in meters for Blender, but correspond to real-life inches if scaled properly.
        """
        # Create parent Empty
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=location)
        parent_obj = bpy.context.object
        parent_obj.name = f"{name_prefix}_Parent"

        # 1) Create Carcass (Sides, Bottom, Back, Stretchers, ToeKick)
        CabinetFactory._create_carcass(
            parent=parent_obj,
            name_prefix=name_prefix,
            cab_width=cabinet_width,
            cab_height=cabinet_height,
            cab_depth=cabinet_depth,
            toe_kick_height=toe_kick_height,
            toe_kick_depth=toe_kick_depth,
            carcass_thickness=carcass_thickness,
            back_thickness=back_thickness,
            is_face_frame=is_face_frame,
            material_carcass=material_carcass
        )

        # 2) Create Face Frame (if is_face_frame)
        if is_face_frame:
            CabinetFactory._create_face_frame(
                parent=parent_obj,
                name_prefix=name_prefix,
                cab_width=cabinet_width,
                cab_height=cabinet_height,
                toe_kick_height=toe_kick_height,
                carcass_thickness=carcass_thickness,
                face_frame_width=face_frame_width,
                material_frame=material_faceframe
            )

        # 3) Create Shelves
        if shelf_count > 0:
            CabinetFactory._create_shelves(
                parent=parent_obj,
                name_prefix=name_prefix,
                cab_width=cabinet_width,
                cab_height=cabinet_height,
                cab_depth=cabinet_depth,
                shelf_count=shelf_count,
                carcass_thickness=carcass_thickness,
                toe_kick_height=toe_kick_height,
                is_face_frame=is_face_frame,
                face_frame_width=face_frame_width,
                material_carcass=material_carcass
            )

        # 4) Create Drawers (including drawer box + 5-piece front)
        if drawer_count > 0:
            CabinetFactory._create_drawers(
                parent=parent_obj,
                name_prefix=name_prefix,
                cab_width=cabinet_width,
                cab_height=cabinet_height,
                cab_depth=cabinet_depth,
                drawer_count=drawer_count,
                carcass_thickness=carcass_thickness,
                door_frame_thickness=door_frame_thickness,
                door_panel_thickness=door_panel_thickness,
                face_frame_width=face_frame_width,
                is_face_frame=is_face_frame,
                toe_kick_height=toe_kick_height,
                material_door=material_door
            )

        # 5) Create Doors (5-piece style if desired)
        if door_count > 0:
            CabinetFactory._create_doors(
                parent=parent_obj,
                name_prefix=name_prefix,
                cab_width=cabinet_width,
                cab_height=cabinet_height,
                cab_depth=cabinet_depth,
                door_count=door_count,
                carcass_thickness=carcass_thickness,
                door_frame_thickness=door_frame_thickness,
                door_panel_thickness=door_panel_thickness,
                face_frame_width=face_frame_width,
                is_face_frame=is_face_frame,
                toe_kick_height=toe_kick_height,
                material_door=material_door
            )

        # 6) Optional Countertop
        if add_countertop:
            CabinetFactory._create_countertop(
                parent=parent_obj,
                name_prefix=name_prefix,
                cab_width=cabinet_width,
                cab_depth=cabinet_depth,
                countertop_thickness=countertop_thickness,
                toe_kick_height=toe_kick_height,
                material_counter=material_counter
            )

        return parent_obj

    # ------------------------------------------------------------------------
    # Carcass: Sides, Bottom, Back, Toe-Kick, Stretchers
    # ------------------------------------------------------------------------
    @staticmethod
    def _create_carcass(
            parent, name_prefix,
            cab_width, cab_height, cab_depth,
            toe_kick_height, toe_kick_depth,
            carcass_thickness, back_thickness,
            is_face_frame,
            material_carcass
    ):
        """
        Creates:
          - 2 side panels (with toe-kick notches)
          - bottom panel
          - back panel
          - top stretchers
          - toe-kick board
        """
        # 1) Side Panels
        # The actual side panel height includes the full cab_height
        # We'll notch out toe-kick from the bottom front.
        # For simplicity, let's not boolean cut the side, but let's visually place it to mimic the shape.

        # Side panel full dimension:
        # Height = cab_height
        # Depth = carcass_thickness
        # 'Width' (in local usage) = cab_depth (front to back)
        # We'll place them at +/- cab_width/2 in X
        side_nameL = f"{name_prefix}_SideLeft"
        side_objL = create_board(
            name=side_nameL,
            width=cab_depth,  # local X
            height=cab_height,  # local Y
            thickness=carcass_thickness,  # local Z
            location=(-cab_width / 2 + carcass_thickness / 2, 0, cab_height / 2),
            parent=parent,
            material=material_carcass
        )

        side_nameR = f"{name_prefix}_SideRight"
        side_objR = create_board(
            name=side_nameR,
            width=cab_depth,
            height=cab_height,
            thickness=carcass_thickness,
            location=(cab_width / 2 - carcass_thickness / 2, 0, cab_height / 2),
            parent=parent,
            material=material_carcass
        )

        # 2) Bottom Panel
        # Typically sits at the top of toe_kick. So bottom panel's Y= depth, X= (cab_width - 2*carcass_thickness)
        # We'll put it flush to inside edges of side panels.
        # Real build uses a dado in side panels, so we can visually just place it there.
        bottom_name = f"{name_prefix}_BottomPanel"
        bottom_obj = create_board(
            name=bottom_name,
            width=(cab_width - 2 * carcass_thickness),  # local X
            height=(cab_depth),  # local Y
            thickness=carcass_thickness,  # local Z
            location=(0, 0, toe_kick_height + carcass_thickness / 2),
            parent=parent,
            material=material_carcass
        )

        # 3) Back Panel
        # Thinner 1/4\". Typically inside the side panels and rests on top of bottom panel or in a rabbet.
        back_name = f"{name_prefix}_BackPanel"
        back_obj = create_board(
            name=back_name,
            width=(cab_width - 2 * carcass_thickness),
            height=(cab_height - toe_kick_height),  # from top of toe-kick to top
            thickness=back_thickness,
            location=(0, -cab_depth / 2 + back_thickness / 2, toe_kick_height + (cab_height - toe_kick_height) / 2),
            parent=parent,
            material=material_carcass
        )

        # 4) Toe-Kick Board
        # placed at bottom front, bridging side panels horizontally.
        # height = toe_kick_height, thickness = carcass_thickness, width ~ inside side panels
        toe_name = f"{name_prefix}_ToeKick"
        toe_obj = create_board(
            name=toe_name,
            width=(cab_width - 2 * carcass_thickness),
            height=toe_kick_height,
            thickness=carcass_thickness,
            location=(0, cab_depth / 2 - toe_kick_depth / 2, toe_kick_height / 2),
            parent=parent,
            material=material_carcass
        )

        # 5) Top Stretcher(s)
        # Many builds have a back stretcher behind the top, plus a front stretcher in frameless style.
        # For face-frame style, front is covered by face frame. Let's at least do a back stretcher:
        stretcher_height = 0.1016  # ~4\" typical
        # Limit so we don't exceed cabinet top
        if stretcher_height > (cab_height - toe_kick_height):
            stretcher_height = (cab_height - toe_kick_height) / 2
        top_stretcher_name = f"{name_prefix}_BackStretcherTop"
        top_stretcher_obj = create_board(
            name=top_stretcher_name,
            width=(cab_width - 2 * carcass_thickness),
            height=stretcher_height,
            thickness=carcass_thickness,
            location=(0, -cab_depth / 2 + carcass_thickness / 2, cab_height - stretcher_height / 2),
            parent=parent,
            material=material_carcass
        )

        # (Optional) front stretcher if frameless
        if not is_face_frame:
            front_stretcher_name = f"{name_prefix}_FrontStretcherTop"
            front_stretcher_obj = create_board(
                name=front_stretcher_name,
                width=(cab_width - 2 * carcass_thickness),
                height=stretcher_height,
                thickness=carcass_thickness,
                location=(0, cab_depth / 2 - carcass_thickness / 2, cab_height - stretcher_height / 2),
                parent=parent,
                material=material_carcass
            )

    # ------------------------------------------------------------------------
    # Face Frame
    # ------------------------------------------------------------------------
    @staticmethod
    def _create_face_frame(
            parent, name_prefix,
            cab_width, cab_height,
            toe_kick_height, carcass_thickness,
            face_frame_width,
            material_frame
    ):
        """
        Creates a simple face frame with left/right stiles and top/bottom rails.
        Additional rails could be added for drawers.
        """
        # We'll create 4 main pieces: left stile, right stile, top rail, bottom rail
        # Then a mid rail if there's a drawer. This is simplified, but enough to illustrate the concept.
        frame_thick = carcass_thickness  # Typically ~3/4\"
        # Left Stile
        stile_left = create_board(
            name=f"{name_prefix}_Frame_StileLeft",
            width = face_frame_width,  # local X
            height = (cab_height),  # local Y
            thickness = frame_thick,  # local Z
            location = (-cab_width / 2 + face_frame_width / 2, 0, cab_height / 2),
            parent = parent,
            material = material_frame
        )
        # Right Stile
        stile_right = create_board(
            name=f"{name_prefix}_Frame_StileRight",
            width = face_frame_width,
            height = (cab_height),
            thickness = frame_thick,
            location = (cab_width / 2 - face_frame_width / 2, 0, cab_height / 2),
            parent = parent,
            material = material_frame
        )
        # Top Rail
        rail_top = create_board(
            name=f"{name_prefix}_Frame_RailTop",
            width = (cab_width - 2 * face_frame_width),
            height = face_frame_width,
            thickness = frame_thick,
            location = (0, 0, cab_height - face_frame_width / 2),
            parent = parent,
            material = material_frame
        )
        # Bottom Rail (above toe-kick line)
        # Some builds place this rail at top of toe-kick, or flush with bottom. We'll do top of toe-kick
        rail_bottom = create_board(
            name=f"{name_prefix}_Frame_RailBottom",
            width = (cab_width - 2 * face_frame_width),
            height = face_frame_width,
            thickness = frame_thick,
            location = (0, 0, toe_kick_height + face_frame_width / 2),
            parent = parent,
            material = material_frame
        )

        # ------------------------------------------------------------------------
        # Shelves
        # ------------------------------------------------------------------------
        @staticmethod
        def _create_shelves(
                parent, name_prefix,
                cab_width, cab_height, cab_depth,
                shelf_count,
                carcass_thickness,
                toe_kick_height,
                is_face_frame,
                face_frame_width,
                material_carcass
        ):
            """
            Creates adjustable or fixed shelves in the main open area (below drawers).
            We'll keep it simple: one compartment with 'shelf_count' shelves.
            """
            # We'll place shelves evenly in the door area: from toe_kick_height up to cabinet top
            # If face frame, we subtract face_frame_width from each side's inside dimension
            inner_width = cab_width - 2 * carcass_thickness
            if is_face_frame:
                inner_width -= 2 * face_frame_width

            # Depth is internal: approx cab_depth - carcass_thickness
            inner_depth = cab_depth - carcass_thickness

            compartment_height = cab_height - toe_kick_height
            # We'll evenly distribute shelves in that vertical space:
            for i in range(1, shelf_count + 1):
                frac = i / (shelf_count + 1)
                shelf_z = toe_kick_height + frac * (compartment_height)
                shelf_obj = create_board(
                    name=f"{name_prefix}_Shelf_{i}",
                    width = inner_width,
                    height = inner_depth,
                    thickness = carcass_thickness,
                    location = (0, 0, shelf_z),
                    parent = parent,
                    material = material_carcass
                )

        # ------------------------------------------------------------------------
        # Drawers (Box + 5-piece Front)
        # ------------------------------------------------------------------------
        @staticmethod
        def _create_drawers(
                        parent, name_prefix,
                        cab_width, cab_height, cab_depth,
                        drawer_count,
                        carcass_thickness,
                        door_frame_thickness,
                        door_panel_thickness,
                        face_frame_width,
                        is_face_frame,
                        toe_kick_height,
                        material_door
                ):
                    """
                    We create 'drawer_count' drawers, each with:
                    - A box (4 sides + bottom) for each drawer
                    - A 5-piece front (2 stiles, 2 rails, 1 panel)
                    We'll stack them vertically above the toe kick.
                    """
                    # We'll assume a consistent vertical stack of drawers in the top half of the cabinet,
                    # from e.g. toe_kick_height+some_offset up to near top.
                    # This is simplified. In real builds, you might have a separate section for doors + drawers.
                    total_drawer_zone = cab_height - toe_kick_height
                    drawer_zone_start = toe_kick_height
                    # Each drawer front might be about total_drawer_zone/drawer_count in height
                    each_drawer_height = total_drawer_zone / drawer_count

                    # Internal box dims (width a bit narrower than internal by e.g. slides):
                    # If face frame, subtract 2*(face_frame_width)
                    inside_width = cab_width - 2 * carcass_thickness
                    if is_face_frame:
                        inside_width -= 2 * face_frame_width

                    inside_depth = cab_depth - carcass_thickness
                    # Let's assume drawer box thickness is the same as carcass_thickness

                    for i in range(drawer_count):
                        # Drawer i vertical middle
                        y_mid = drawer_zone_start + (i + 0.5) * each_drawer_height
                        # 1) Drawer box
                        # We'll create the box as one piece for simplicity, but you can separate sides if needed
                        box_name = f"{name_prefix}_DrawerBox_{i}"
                        box_obj = create_board(
                            name=box_name,
                            width=inside_width * 0.95,  # leave some side clearance
                            height=inside_depth * 0.95,  # short of full depth for clearance
                            thickness=carcass_thickness * 0.5,  # just a placeholder thickness
                            location=(0, 0, y_mid),
                            parent=parent,
                            material=material_door
                        )
                        # 2) Drawer Front (5-piece). We'll keep it simple: we only model it as a separate assembly
                        # Assume overlay or flush with face frame. The height = each_drawer_height with small gap
                        front_height = each_drawer_height * 0.9  # small gap
                        front_width = cab_width if not is_face_frame else (cab_width - face_frame_width * 0.2)
                        # We'll create stiles/rails/panel
                        CabinetFactory._create_5piece_front(
                            parent=parent,
                            name_prefix=f"{name_prefix}_DrawerFront_{i}",
                            width = front_width,
                            height = front_height,
                            frame_thickness = door_frame_thickness,
                            panel_thickness = door_panel_thickness,
                            center_x = 0,
                            center_z = (y_mid),  # center
                            location_depth = (cab_depth / 2))


        # ------------------------------------------------------------------------
        # Doors (5-piece)
        # ------------------------------------------------------------------------
        @staticmethod
        def _create_doors(
                                parent, name_prefix,
                                cab_width, cab_height, cab_depth,
                                door_count,
                                carcass_thickness,
                                door_frame_thickness,
                                door_panel_thickness,
                                face_frame_width,
                                is_face_frame,
                                toe_kick_height,
                                material_door
                        ):
                            """
                            Creates 'door_count' 5-piece doors along the front.
                            If door_count=1, a single door. If 2, double doors.
                            For simplicity, place them from left to right, each covering half or portion of front.
                            """
                            # We'll place them below the drawers (or total if no drawers).
                            door_zone_top = cab_height
                            # If we have drawers, let's guess they're stacked in top half. We'll put doors in bottom half.
                            # This is simplistic, but a good example.

                            # We'll place them from left to right.
                            # Each door covers (cab_width / door_count) wide in front, from toe_kick_height to near half the cabinet.
                            door_height = door_zone_top - toe_kick_height
                            each_door_width = cab_width / door_count

                            for i in range(door_count):
                                door_center_x = -cab_width / 2 + each_door_width * (i + 0.5)
                                door_name = f"{name_prefix}_Door_{i}"

                                # We'll create a 5-piece assembly
                                CabinetFactory._create_5piece_front(
                                    parent=parent,
                                    name_prefix=door_name,
                                    width=each_door_width * 0.95,  # small gap
                                    height=door_height * 0.95,
                                    frame_thickness=door_frame_thickness,
                                    panel_thickness=door_panel_thickness,
                                    center_x=door_center_x,
                                    center_z=(toe_kick_height + door_height / 2),
                                    location_depth=(cab_depth / 2),
                                    material=material_door
                                )

        # ------------------------------------------------------------------------
        # 5-Piece Front (Door/Drawer)
        # ------------------------------------------------------------------------
        @staticmethod
        def _create_5piece_front(
                                parent, name_prefix,
                                width, height,
                                frame_thickness,
                                panel_thickness,
                                center_x, center_z,
                                location_depth,
                                material
                        ):
                            """
                            Creates a 5-piece style assembly (2 stiles, 2 rails, 1 center panel).
                            Positions at (center_x, location_depth, center_z) in parent's space.
                            This is used for both doors and drawer fronts.
                            """

                            # We'll create an Empty to group them
                            bpy.ops.object.empty_add(type='PLAIN_AXES', location=(center_x, location_depth, center_z))
                            front_parent = bpy.context.object
                            front_parent.name = f"{name_prefix}_5PieceParent"
                            front_parent.parent = parent

                            # Stiles: vertical
                            stile_width = frame_thickness
                            stile_height = height
                            # place left stile
                            left_stile_x = -width / 2 + stile_width / 2
                            left_stile = create_board(
                                name=f"{name_prefix}_StileLeft",
                                width = stile_width,
                                height = stile_height,
                                thickness = frame_thickness,
                                location = (left_stile_x, 0, 0),
                                parent = front_parent,
                                material = material
                            )
                            # right stile
                            right_stile_x = width / 2 - stile_width / 2
                            right_stile = create_board(
                                name=f"{name_prefix}_StileRight",
                                width = stile_width,
                                height = stile_height,
                                thickness = frame_thickness,
                                location = (right_stile_x, 0, 0),
                                parent = front_parent,
                                material = material
                            )

                            # Rails: horizontal
                            rail_height = frame_thickness
                            rail_width = width - 2 * stile_width
                            # top rail
                            top_rail_y = height / 2 - rail_height / 2
                            top_rail = create_board(
                                name=f"{name_prefix}_RailTop",
                                width = rail_width,
                                height = rail_height,
                                thickness = frame_thickness,
                                location = (0, 0, top_rail_y),
                                parent = front_parent,
                                material = material
                            )
                            # bottom rail
                            bot_rail_y = -height / 2 + rail_height / 2
                            bot_rail = create_board(
                                name=f"{name_prefix}_RailBottom",
                                width = rail_width,
                                height = rail_height,
                                thickness = frame_thickness,
                                location = (0, 0, bot_rail_y),
                                parent = front_parent,
                                material = material
                            )

                            # Center Panel
                            # Typically about (rail_width) wide, (height - 2*frame_thickness) tall, thickness=panel_thickness
                            panel_w = rail_width
                            panel_h = height - 2 * frame_thickness
                            panel_name = f"{name_prefix}_Panel"
                            panel = create_board(
                                name=panel_name,
                                width=panel_w,
                                height=panel_h,
                                thickness=panel_thickness,
                                location=(0, 0, 0),
                                parent=front_parent,
                                material=material
                            )
                            # Optionally we can shift the panel slightly backward to appear recessed:
                            # panel.location.z = -0.002 # offset in local space if you want a recess

                        # ------------------------------------------------------------------------
                        # Countertop
                        # ------------------------------------------------------------------------
        @staticmethod
        def _create_countertop(
                                parent, name_prefix,
                                cab_width, cab_depth,
                                countertop_thickness,
                                toe_kick_height,
                                material_counter
                        ):
                            """
                            Creates a simple rectangular countertop above the cabinet.
                            Usually extends the full width & depth, or a slight overhang. We'll do a small overhang.
                            """
                            overhang = 0.025  # ~1 inch overhang
                            top_z = toe_kick_height + 0.9  # default cabinet height 0.9, but better to param it in the real code
                            # If we want to measure the actual side panels for exact top, we would do so. We'll assume 0.9 for now.
                            ctop_name = f"{name_prefix}_Countertop"
                            ctop = create_board(
                                name=ctop_name,
                                width=(cab_width + 2 * overhang),
                                height=(cab_depth + overhang),
                                thickness=countertop_thickness,
                                location=(0, 0, top_z + countertop_thickness / 2),
                                parent=parent,
                                material=material_counter)



# ----------------------------------------------------------------------------
# Example usage in Blender
# ----------------------------------------------------------------------------
def main():
        # Ensure we run inside Blender
        if not bpy.context.scene:
                print("❌ This script must be run inside Blender.")
                return

                        # Sample creation of a base face-frame cabinet
                CabinetFactory.create_cabinet(
                            name_prefix="BaseCabFF",
                            location = (0, 0, 0),
                            cabinet_width = 0.9,  # 90cm ~ 35.4in
                            cabinet_height = 0.9,  # standard 34.5in base height ignoring countertop thickness
                            cabinet_depth = 0.6,  # ~24in
                            is_face_frame = True,
                            toe_kick_height = 0.1143,  # 4.5\"
                            toe_kick_depth = 0.0762,  # 3\"
                            shelf_count = 1,
                            drawer_count = 1,
                            door_count = 1,
                        )

                # Another example: Frameless upper cabinet
                CabinetFactory.create_cabinet(
                            name_prefix="WallCabFrameless",
                            location = (2, 0, 1),  # offset in X=2, Z=1
                            cabinet_width = 0.8,
                            cabinet_height = 0.7,
                            cabinet_depth = 0.35,
                            is_face_frame = False,
                            toe_kick_height = 0,  # no toe-kick for uppers
                            toe_kick_depth = 0,
                            add_countertop = False,
                            shelf_count = 2,
                            drawer_count = 0,
                                                                                                                                                       door_count = 2,
                        )

if __name__ == "__main__":
            main()
