import bpy

# Clear existing objects in the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create materials for visual distinction
material_framing = bpy.data.materials.new(name="Framing")
material_framing.diffuse_color = (0.8, 0.6, 0.4, 1)  # Light brown for framing

material_panel = bpy.data.materials.new(name="Panel")
material_panel.diffuse_color = (1, 1, 1, 1)  # White for panels

material_shelf = bpy.data.materials.new(name="Shelf")
material_shelf.diffuse_color = (1, 1, 1, 1)  # White for shelves

material_door = bpy.data.materials.new(name="Door")
material_door.diffuse_color = (0.4, 0.6, 0.8, 1)  # Light blue for doors

material_face_frame = bpy.data.materials.new(name="FaceFrame")
material_face_frame.diffuse_color = (0.6, 0.4, 0.2, 1)  # Darker brown for face frame

# Create parent empty object
bpy.ops.object.empty_add(location=(0, 0, 0))
parent_empty = bpy.context.object
parent_empty.name = "Cabinet_Parent"

# Function to create and parent objects
def create_object(location, scale, material, name, parent):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.scale = scale
    obj.data.materials.append(material)
    obj.name = name
    obj.parent = parent
    return obj

# Cabinet dimensions
cabinet_width = 24
cabinet_depth = 24
cabinet_height = 35

# Create two cabinets side by side
for i in range(2):
    x_offset = i * cabinet_width

    # Create vertical framing members (2x3s)
    vertical_front_left = create_object(
        location=(x_offset + 0.75, 17.5, 1.25),
        scale=(0.75, 17.5, 1.25),
        material=material_framing,
        name=f"Vertical_Front_Left_{i}",
        parent=parent_empty
    )
    vertical_front_right = create_object(
        location=(x_offset + cabinet_width - 0.75, 17.5, 1.25),
        scale=(0.75, 17.5, 1.25),
        material=material_framing,
        name=f"Vertical_Front_Right_{i}",
        parent=parent_empty
    )
    vertical_back_left = create_object(
        location=(x_offset + 0.75, 17.5, cabinet_depth - 1.25),
        scale=(0.75, 17.5, 1.25),
        material=material_framing,
        name=f"Vertical_Back_Left_{i}",
        parent=parent_empty
    )
    vertical_back_right = create_object(
        location=(x_offset + cabinet_width - 0.75, 17.5, cabinet_depth - 1.25),
        scale=(0.75, 17.5, 1.25),
        material=material_framing,
        name=f"Vertical_Back_Right_{i}",
        parent=parent_empty
    )

    # Create horizontal braces (top and bottom)
    for y in [0.75, 33.75]:
        brace_front = create_object(
            location=(x_offset + cabinet_width / 2, y, 1.25),
            scale=(cabinet_width / 2 - 1.5, 0.75, 1.25),
            material=material_framing,
            name=f"Brace_Front_{i}_{y}",
            parent=parent_empty
        )
        brace_back = create_object(
            location=(x_offset + cabinet_width / 2, y, cabinet_depth - 1.25),
            scale=(cabinet_width / 2 - 1.5, 0.75, 1.25),
            material=material_framing,
            name=f"Brace_Back_{i}_{y}",
            parent=parent_empty
        )
        brace_left = create_object(
            location=(x_offset + 0.75, y, cabinet_depth / 2),
            scale=(0.75, 0.75, cabinet_depth / 2 - 2.5),
            material=material_framing,
            name=f"Brace_Left_{i}_{y}",
            parent=parent_empty
        )
        brace_right = create_object(
            location=(x_offset + cabinet_width - 0.75, y, cabinet_depth / 2),
            scale=(0.75, 0.75, cabinet_depth / 2 - 2.5),
            material=material_framing,
            name=f"Brace_Right_{i}_{y}",
            parent=parent_empty
        )

    # Create side panels
    if i == 0:
        side_panel_left = create_object(
            location=(x_offset, 17.5, cabinet_depth / 2),
            scale=(0.375, 17.5, cabinet_depth / 2),
            material=material_panel,
            name="Side_Panel_Left",
            parent=parent_empty
        )
    if i == 1:
        side_panel_right = create_object(
            location=(x_offset + cabinet_width, 17.5, cabinet_depth / 2),
            scale=(0.375, 17.5, cabinet_depth / 2),
            material=material_panel,
            name="Side_Panel_Right",
            parent=parent_empty
        )
    # Middle side panels for each cabinet
    side_panel_middle = create_object(
        location=(x_offset + cabinet_width, 17.5, cabinet_depth / 2),
        scale=(0.375, 17.5, cabinet_depth / 2),
        material=material_panel,
        name=f"Side_Panel_Middle_{i}",
        parent=parent_empty
    )

    # Create back panel
    back_panel = create_object(
        location=(x_offset + cabinet_width / 2, 17.5, cabinet_depth - 0.375),
        scale=(cabinet_width / 2, 17.5, 0.375),
        material=material_panel,
        name=f"Back_Panel_{i}",
        parent=parent_empty
    )

    # Create bottom panel
    bottom_panel = create_object(
        location=(x_offset + cabinet_width / 2, 0.375, cabinet_depth / 2),
        scale=(cabinet_width / 2, 0.375, cabinet_depth / 2),
        material=material_panel,
        name=f"Bottom_Panel_{i}",
        parent=parent_empty
    )

    # Create shelf
    shelf = create_object(
        location=(x_offset + cabinet_width / 2, 17.5, cabinet_depth / 2),
        scale=(cabinet_width / 2 - 1.5, 0.375, cabinet_depth / 2 - 1.5),
        material=material_shelf,
        name=f"Shelf_{i}",
        parent=parent_empty
    )

    # Create face frame stiles
    if i == 0:
        stile_left = create_object(
            location=(1, 17.5, 0.375),
            scale=(1, 17.5, 0.375),
            material=material_face_frame,
            name="Face_Stile_Left",
            parent=parent_empty
        )
        stile_middle = create_object(
            location=(24, 17.5, 0.375),
            scale=(1, 17.5, 0.375),
            material=material_face_frame,
            name="Face_Stile_Middle",
            parent=parent_empty
        )
    if i == 1:
        stile_right = create_object(
            location=(47, 17.5, 0.375),
            scale=(1, 17.5, 0.375),
            material=material_face_frame,
            name="Face_Stile_Right",
            parent=parent_empty
        )

    # Create top rail (only once for both cabinets)
    if i == 0:
        top_rail = create_object(
            location=(24, 34, 0.375),
            scale=(24, 1, 0.375),
            material=material_face_frame,
            name="Face_Top_Rail",
            parent=parent_empty
        )

    # Create door
    door_location = (x_offset + cabinet_width / 2, 17, 0.8)
    door_width = 23
    door_height = 34
    stile_width = 1.5
    rail_height = 1.5
    panel_width = door_width - 2 * stile_width
    panel_height = door_height - 2 * rail_height
    door_thickness = 0.75

    # Left stile
    left_stile_x = door_location[0] - door_width / 2 + stile_width / 2
    left_stile = create_object(
        location=(left_stile_x, door_location[1], door_location[2]),
        scale=(stile_width / 2, door_height / 2, door_thickness / 2),
        material=material_door,
        name=f"Door_Left_Stile_{i}",
        parent=None  # Will be joined later
    )

    # Right stile
    right_stile_x = door_location[0] + door_width / 2 - stile_width / 2
    right_stile = create_object(
        location=(right_stile_x, door_location[1], door_location[2]),
        scale=(stile_width / 2, door_height / 2, door_thickness / 2),
        material=material_door,
        name=f"Door_Right_Stile_{i}",
        parent=None
    )

    # Top rail
    top_rail_y = door_location[1] + door_height / 2 - rail_height / 2
    top_rail = create_object(
        location=(door_location[0], top_rail_y, door_location[2]),
        scale=(panel_width / 2, rail_height / 2, door_thickness / 2),
        material=material_door,
        name=f"Door_Top_Rail_{i}",
        parent=None
    )

    # Bottom rail
    bottom_rail_y = door_location[1] - door_height / 2 + rail_height / 2
    bottom_rail = create_object(
        location=(door_location[0], bottom_rail_y, door_location[2]),
        scale=(panel_width / 2, rail_height / 2, door_thickness / 2),
        material=material_door,
        name=f"Door_Bottom_Rail_{i}",
        parent=None
    )

    # Center panel
    panel_z = door_location[2] - door_thickness / 2 + 0.125  # Recessed panel
    panel = create_object(
        location=(door_location[0], door_location[1], panel_z),
        scale=(panel_width / 2, panel_height / 2, 0.125),  # 0.25 thick
        material=material_door,
        name=f"Door_Panel_{i}",
        parent=None
    )

    # Join door components into one object
    bpy.ops.object.select_all(action='DESELECT')
    left_stile.select_set(True)
    right_stile.select_set(True)
    top_rail.select_set(True)
    bottom_rail.select_set(True)
    panel.select_set(True)
    bpy.context.view_layer.objects.active = left_stile
    bpy.ops.object.join()
    door = bpy.context.object
    door.name = f"Door_{i}"
    door.parent = parent_empty

# Update the scene
bpy.context.view_layer.update()