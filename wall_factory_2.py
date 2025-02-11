class WallFactory:
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
    def place_corner_assembly(parent, corner_xy, prev_xy, next_xy, wall_height, materials, corner_name):
        """
        Creates a corner stud "L" (or "U") at 'corner_xy' that meets
        the edges from 'prev_xy->corner_xy' and 'corner_xy->next_xy'.
        """
        (cx, cy) = corner_xy
        (px, py) = prev_xy
        (nx, ny) = next_xy

        # For a standard 90° building corner, this is straightforward,
        # but let's do a more general approach:
        # 1) direction of the previous edge
        dx_prev = cx - px
        dy_prev = cy - py
        ang_prev = math.atan2(dy_prev, dx_prev)

        # 2) direction of the next edge
        dx_next = nx - cx
        dy_next = ny - cy
        ang_next = math.atan2(dy_next, dx_next)

        # The corner angle is ang_next - ang_prev (mod 360)
        # We'll just place an "L" shaped corner stud at the corner,
        # oriented in some average direction or whichever logic you prefer.

        # We'll put an Empty at the corner coords
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=(cx, cy, 0))
        corner_parent = bpy.context.object
        corner_parent.name = corner_name
        corner_parent.parent = parent

        # For a very simplistic approach:
        # We'll align the corner so that the "bisector" is the parent's local X
        corner_bisect = (ang_next + ang_prev) / 2.0
        corner_parent.rotation_euler[2] = corner_bisect

        # Then place 2 or 3 boards forming an L:
        mat_framing = materials.get("framing")
        stud_t = WallFactory.STUD_SPECS["2x4"]["thickness"]
        stud_w = WallFactory.STUD_SPECS["2x4"]["width"]

        # A simple 2-stud L
        # Stud 1
        BoardFactory.add_board(
            parent=corner_parent,
            board_name=f"{corner_name}_Stud1",
            length=stud_t,  # local X
            height=wall_height,
            depth=stud_w,  # local Y
            location=(0, 0, wall_height / 2.0),
            material=mat_framing
        )
        # Stud 2 turned 90°, offset so it touches Stud1
        offset = stud_t
        BoardFactory.add_board(
            parent=corner_parent,
            board_name=f"{corner_name}_Stud2",
            length=stud_w,  # local X
            height=wall_height,
            depth=stud_t,  # local Y
            location=(offset / 2.0, offset / 2.0, wall_height / 2.0),
            material=mat_framing
        )

    @staticmethod
    def create_corner_assembly_2stud(
            corner_name: str,
            pPrev, pCorner, pNext,  # (x,y) for previous vertex, corner vertex, next vertex
            wall_height: float,
            corner_margin: float,
            materials: dict = None
    ):
        """
        Creates a "2-stud advanced framing" corner (California corner).
        - Stud A follows one wall's exterior line.
        - Stud B follows the perpendicular wall's exterior line.
        - Leaves interior corner open for insulation.
        - Optionally add a small horizontal block or "drywall clip" for the interior finish.

        We'll assume typical 90° corners. If the corner angle isn't ~90°,
        you can adapt the logic or do angle checks.
        """

        mat_framing = materials.get('framing') if materials else None

        px, py = pPrev
        cx, cy = pCorner
        nx, ny = pNext

        # Directions of edges
        ang_prev = math.atan2(cy - py, cx - px)
        ang_next = math.atan2(ny - cy, nx - cx)
        corner_angle = (ang_next - ang_prev) % (2 * math.pi)

        # We'll assume it's ~90°:
        deg = math.degrees(corner_angle)
        if abs(deg - 90.0) > 10.0:
            print(f"⚠ Corner at {pCorner} is not near 90°; skipping or adapt code.")
            # For non-right angles, you'd do more advanced geometry.
            pass

        # Create a parent Empty
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=(cx, cy, 0))
        corner_parent = bpy.context.object
        corner_parent.name = corner_name

        # Let's pick one angle as "Wall A" => ang_prev, the other as "Wall B" => ang_next
        # We place 2 studs so that each stud is flush with the *exterior* line of each wall.

        stud_height = wall_height
        stud_A = BoardFactory.add_board(
            parent=corner_parent,
            board_name=f"{corner_name}_StudA",
            length=STUD_THICKNESS,  # local X
            height=stud_height,  # local Z
            depth=STUD_WIDTH,  # local Y
            location=(0, 0, stud_height / 2.0),
            rotation_euler=(0, 0, ang_prev),  # oriented with first wall
            material=mat_framing
        )

        stud_B = BoardFactory.add_board(
            parent=corner_parent,
            board_name=f"{corner_name}_StudB",
            length=STUD_THICKNESS,
            height=stud_height,
            depth=STUD_WIDTH,
            location=(0, 0, stud_height / 2.0),
            rotation_euler=(0, 0, ang_next),  # oriented with second wall
            material=mat_framing
        )

        # Now, both studs meet at the outer corner if you draw them flush to the outside line.
        # The interior corner is open. In real life, you shift each stud by 1/2" or so
        # to match your sheathing plane, but the idea is the same.

        # OPTIONAL: Add "drywall blocking" or "clip" near mid-height
        # so interior drywall can be nailed. We'll do a small board
        # bridging between the two studs, but offset so it doesn't fill the whole corner.
        drywall_clip_height = wall_height / 2.0
        bridging_length = 0.15  # just 15 cm? Enough for a small nailing surface

        # We'll place it so it's "horizontal" in local space and oriented
        # bridging from stud A to stud B
        # We'll compute a midpoint angle halfway between ang_prev & ang_next
        bisect_angle = ang_prev + (corner_angle / 2.0)
        # Place a short piece bridging the interior gap
        # We won't do perfect math for the offset; just a small representation:
        BoardFactory.add_board(
            parent=corner_parent,
            board_name=f"{corner_name}_DrywallBlocking",
            length=bridging_length,  # local X
            height=STUD_THICKNESS / 2.0,  # just a half-thickness block
            depth=STUD_WIDTH,  # local Y
            location=(0.05, 0.05, drywall_clip_height),  # arbitrary offset
            rotation_euler=(0, 0, bisect_angle),
            material=mat_framing
        )

        return corner_parent

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