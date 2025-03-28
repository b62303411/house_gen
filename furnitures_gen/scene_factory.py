import math
import bpy

from furnitures_gen.furniture_factory import FurnitureFactory
from house_factory import HouseFactory
from materials import MaterialFactory
from node_render import NodeRender
from textured_plane_factory import TexturedPlaneFactory

class SceneFactory:
    @staticmethod
    def build_entire_perimeter_example():
            # Example footprint: a rectangular building
            footprint_points = [
                (0, 0),
                (15, 0),
                (15, 10),
                (0, 10)
            ]

            # Materials
            mats = MaterialFactory.create_materials()
            ws = [
                {"center_x": -3, "bottom_z": 0.5, "width": 1.5, "height": 2},
                {"center_x": 0, "bottom_z": 0.5, "width": 1.5, "height": 2},
                {"center_x": 3, "bottom_z": 0.5, "width": 1.5, "height": 2}
            ]
            windows_spec = []
            windows_spec.append(ws)
            windows_spec.append(ws)
            windows_spec.append(ws)
            windows_spec.append(ws)

            # Create the outer wall with segments & corners
            wall_parent = HouseFactory.create_outer_wall(
                name="OuterWall",
                footprint_points=footprint_points,
                wall_height=3.0,
                stud_spacing=0.4064,
                materials=mats,
                windows_spec=windows_spec
            )
            living_room = [
                (0, 0),
                (9, 0),
                (9, 3),
                (0, 3)
            ]
            HouseFactory.create_inner_wall(
                name="Livingroom",
                footprint_points=living_room,
                wall_height=3.0,
                stud_spacing=0.4064,
                materials=mats,
                doors_spec=None
            )

            print("✅ Finished building single multi-segment outer wall with corners.")

    @staticmethod
    def create_furniture():
        #FurnitureFactory.create_furniture_prototypes()
        FurnitureFactory.place_furniture()
    @staticmethod
    def create_from_json():
        FurnitureFactory.create_furniture_prototypes()
        NodeRender.build_from_data()



    # Function to create a marker (empty object) at a given position
    @staticmethod
    def create_marker(location, name):
        bpy.ops.object.empty_add(type='SPHERE', radius=0.2, location=location)
        marker = bpy.context.object
        marker.name = name
    @staticmethod
    def create_plane_plan():
        #bpy.ops.mesh.primitive_plane_add(size=1)
        obj = TexturedPlaneFactory.create_textured_plane("/w1024.jpg", "architecture plan")
        obj.name = "architecture plan"
        obj.location = (0.375159,-0.842076 ,0)
        # Correct scaling
        #obj.scale = (20, 12, 1 )# Ensure full size scaling

        # Apply scale
        #bpy.ops.object.transform_apply(scale=True, location=False)
    @staticmethod
    def build_scene():
        # demo_wall_test()
        #SceneFactory.build_entire_perimeter_example()
        SceneFactory.create_plane_plan()
        SceneFactory.create_from_json()
        #SceneFactory.create_furniture()
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