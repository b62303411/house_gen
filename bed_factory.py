import bpy
from materials import MaterialFactory
import math
import bmesh
from math import radians


def enable_collision(obj, thickness_outer=0.02, friction=80.0):
    """Enable collision on the given object for cloth/physics simulation."""
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_add(type='COLLISION')
    col_mod = obj.modifiers[-1]
    col_mod.settings.thickness_outer = thickness_outer
    col_mod.settings.cloth_friction = friction
    # List all attributes of the collision settings
    #if hasattr(col_mod, 'settings'):
    #    print("\nCollision settings attributes:")
    #    print(dir(col_mod.settings))


def add_bevel_modifier(obj, width=0.05, segments=2, angle=45.0):
    """Adds and applies a bevel modifier to round off sharp edges."""
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_add(type='BEVEL')

    bevel_mod = obj.modifiers["Bevel"]
    bevel_mod.limit_method = 'ANGLE'
    bevel_mod.angle_limit = math.radians(angle)
    bevel_mod.width = width
    bevel_mod.segments = segments

    # Apply the bevel so the geometry actually changes (good for collisions)
    bpy.ops.object.modifier_apply(modifier="Bevel")


class BedFactory:
    @staticmethod
    def create_fold(obj):
        # Get a BMesh representation of the mesh
        bm = bmesh.from_edit_mesh(obj.data)
        axis = 'x'
        direction = 1
        # Determine the coordinate to use based on the axis
        if axis == 'x':
            coord_index = 0  # X-axis
        elif axis == 'y':
            coord_index = 1  # Y-axis
        else:
            print("Invalid axis. Use 'x' or 'y'.")
            return

        # Find the maximum or minimum coordinate along the selected axis
        if direction == 1:
            target_coord = max(v.co[coord_index] for v in bm.verts)
        else:
            target_coord = min(v.co[coord_index] for v in bm.verts)

        # Select edges that are close to the target coordinate
        tolerance = 0.01  # Adjust this value as needed
        target_edges = [
            e for e in bm.edges
            if any(abs(v.co[coord_index] - target_coord) < tolerance for v in e.verts)
        ]

        # Ensure only one edge is selected
        if not target_edges:
            print("No target edge found.")
            return
        selected_edge = target_edges[0]  # Select the first edge in the list
        # Select the edge facing the top of the bed
        # For example, select the edge with the highest Z-coordinate
        #selected_edge = max(bm.edges, key=lambda e: max(v.co.z for v in e.verts))
        selected_edge.select = True

        # Perform iterative extrusion and rotation
        for i in range(6):  # 6 iterations
            # Extrude the selected edge
            extruded = bmesh.ops.extrude_edge_only(bm, edges=[e for e in bm.edges if e.select])

            # Rotate the extruded geometry upward and backward
            #bmesh.ops.rotate(
            #    bm,
            #    verts=extruded['geom'],
            #    cent=selected_edge.verts[0].co,  # Rotate around the first vertex of the edge
            #    matrix=radians(15),  # Rotate by 15 degrees per iteration
            #    space=obj.matrix_world,
            #)

            # Move the extruded geometry slightly upward
            bmesh.ops.translate(
                bm,
                vec=(0, 0, 0.05),  # Move upward along the Z-axis
                verts=extruded['geom'],
            )

            # Update the selection for the next iteration
            selected_edge = extruded['geom'][0]  # Select the newly extruded edge

        # Update the mesh
        bmesh.update_edit_mesh(obj.data)

    @staticmethod
    def create_bed(name="Bed", length=2.03, width=1.93, height=0.5,
                   materials=None, mattress_bevel=0.06, location=(0, 0, 0)):
        """Creates a simple bed frame with a headboard and drape.
           Everything is parented to an Empty object ('bed_parent').
        """
        # ----------------------------------------------------
        # (1) Create Materials
        # ----------------------------------------------------
        board_mat = MaterialFactory.create_acajou_wood_material()
        matrice_mat = MaterialFactory.create_matrice_material()
        drape_mat = MaterialFactory.create_drape_material()

        # ----------------------------------------------------
        # (2) Create a Parent Empty
        # ----------------------------------------------------
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=location)
        bed_parent = bpy.context.object
        bed_parent.name = name

        # ----------------------------------------------------
        # (3) Create Mattress
        # ----------------------------------------------------
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
        mattress = bpy.context.object
        mattress.name = f"{name}_Mattress"

        # Scale, apply transforms, then position
        mattress.scale = (length, width, height / 2)
        bpy.ops.object.transform_apply(scale=True)
        mattress.location = (0, 0, height / 4 + 0.1)
        # Optional: Add a geometry bevel to round the mattress edges
        # (so it's not a perfect cube silhouette)
        add_bevel_modifier(mattress, width=mattress_bevel, segments=2, angle=45.0)

        # Enable collision, apply material, then parent
        enable_collision(mattress)
        if matrice_mat:
            MaterialFactory.apply_material(mattress, matrice_mat)
        mattress.parent = bed_parent

        # ----------------------------------------------------
        # (4) Create Headboard
        # ----------------------------------------------------
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
        headboard = bpy.context.object
        headboard.name = f"{name}_Headboard"

        # Scale, apply transforms, then position
        headboard.scale = (0.05, width, height)
        bpy.ops.object.transform_apply(scale=True)
        headboard.location = (length / 2, 0, height / 2)

        # Enable collision, apply material, then parent
        enable_collision(headboard)
        if board_mat:
            MaterialFactory.apply_material(headboard, board_mat)
        headboard.parent = bed_parent

        # ----------------------------------------------------
        # (5) Create Bed Frame Board
        # ----------------------------------------------------
        board_thickness = 0.1
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
        board = bpy.context.object
        board.name = f"{name}_Board"

        # Scale, apply transforms, then position
        board.scale = (length + board_thickness, width + board_thickness, board_thickness)
        bpy.ops.object.transform_apply(scale=True)
        board.location = (0, 0, board_thickness / 2)

        # Enable collision, apply material, then parent
        enable_collision(board)
        if board_mat:
            MaterialFactory.apply_material(board, board_mat)
        board.parent = bed_parent

        # ----------------------------------------------------
        # (6) Create Drape (Cloth)
        # ----------------------------------------------------
        bpy.ops.mesh.primitive_plane_add(size=1, location=(-0.1, 0, 0))
        drape = bpy.context.object
        drape.name = f"{name}_Drape"

        # Scale, apply transforms, then position
        drape.scale = (length + 0.2, width + 0.2, 1)
        bpy.ops.object.transform_apply(scale=True)
        drape.location = (0, 0, height / 2 + 0.15)

        # Apply material, parent
        if drape_mat:
            MaterialFactory.apply_material(drape, drape_mat)
        drape.parent = bed_parent

        # Subdivide the drape for better cloth simulation
        bpy.context.view_layer.objects.active = drape
        bpy.ops.object.mode_set(mode='EDIT')
        #BedFactory.create_fold(drape)
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.subdivide(number_cuts=100)
        bpy.ops.object.mode_set(mode='OBJECT')
        # Enable Cloth Physics
        bpy.context.view_layer.objects.active = drape

        enable_collision(drape)
        bpy.ops.object.modifier_add(type='CLOTH')
        cloth_modifier = drape.modifiers["Cloth"]

        cloth_modifier.settings.quality = 10
        cloth_modifier.settings.tension_stiffness = 15
        cloth_modifier.settings.compression_stiffness = 15
        cloth_modifier.settings.bending_stiffness = 10
        cloth_modifier.settings.use_pressure = False  # for an open drape

        # Enable self-collision & object-collision
        cloth_modifier.collision_settings.use_self_collision = True
        cloth_modifier.collision_settings.self_distance_min = 0.01
        cloth_modifier.collision_settings.distance_min = 0.01
        cloth_modifier.collision_settings.friction = 80.0

        # (Optional) Example: adding a normal map node in the Drape's material
        if drape.data.materials:
            material = drape.data.materials[0]
            if material.node_tree:
                nodes = material.node_tree.nodes
                tex_image_normal = nodes.new(type='ShaderNodeTexImage')
                tex_image_normal.label = "NormalMapExample"
                # Connect or configure nodes as needed

            # Run the simulation for 30 seconds
        print("Running cloth simulation for 30 seconds...")
        bpy.context.scene.frame_end = 30 * bpy.context.scene.render.fps  # 30 seconds
        bpy.ops.screen.animation_play()  # Start the simulation
        # Bake the cloth simulation
        print("Baking cloth simulation...")
        bpy.ops.ptcache.bake_all(bake=True)  # Bake all physics caches

        # Wait for the bake to complete
        print("Waiting for bake to complete...")
        while bpy.context.scene.frame_current < bpy.context.scene.frame_end:
            bpy.context.scene.frame_set(bpy.context.scene.frame_current + 1)
        # Use a timer to wait for the simulation to finish
        def apply_cloth_modifier():
            # Stop the simulation
            bpy.ops.screen.animation_cancel()

            # Apply the Cloth modifier
            print("Applying Cloth modifier...")
            bpy.ops.object.modifier_apply(modifier="Cloth")

            # Create the fold
            print("Creating fold...")
            #create_fold(drape, axis='y', direction=1)

        # Schedule the apply_cloth_modifier function to run after 30 seconds
        bpy.app.timers.register(apply_cloth_modifier, first_interval=60)

        return bed_parent


# ---------------------------------------------------------------------
# Example Usage (Run from Blender's Text Editor or a .py script)
# ---------------------------------------------------------------------
if __name__ == "__main__":
    # 1) Set scene to start at frame 0
    bpy.context.scene.frame_start = 0
    bpy.context.scene.frame_set(0)

    # 2) Set total animation length to 30 seconds
    #    For example, if your FPS is 24 -> 30s * 24 = 720 frames
    fps = bpy.context.scene.render.fps
    bpy.context.scene.frame_end = 30 * fps

    # 3) Create the Bed
    BedFactory.create_bed()

    # 4) (Optional) Automatically play the animation to let cloth sim run:
    #    (You can comment this out if you want to step through frames manually.)
    #bpy.ops.screen.animation_play()
