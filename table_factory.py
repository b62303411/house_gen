import bpy
from mathutils import Vector

from materials import MaterialFactory


class TableFactory:

        @staticmethod
        def create_table(name="Table", length=2.0, width=1.0, height=0.75, top_thikness=0.05, legs_thikness=0.1, material=None, location=(0, 0, 0)):
            """Creates a simple rectangular table with a parent-child hierarchy and properly positioned tabletop."""

            # Create an empty object as the parent
            bpy.ops.object.empty_add(type='PLAIN_AXES', location=location)
            table_parent = bpy.context.object
            table_parent.name = name
            table_parent.location = location

            # Tabletop
            bpy.ops.mesh.primitive_cube_add(size=1)
            table_top = bpy.context.object
            table_top.name = f"{name}_Top"
            table_top.scale = (length , width , top_thikness)
            table_top.parent = table_parent
            bpy.ops.object.transform_apply(scale=True)
            table_top.location = (0, 0, height)

            if material:
                MaterialFactory.apply_material(table_top, material)
            half_lenght= length / 2
            half_width = width / 2
            # Legs
            leg_positions = [
                (half_lenght-legs_thikness, half_width-legs_thikness , height / 2),
                (-half_lenght+legs_thikness, half_width -legs_thikness, height / 2),
                (half_lenght-legs_thikness, -half_width+legs_thikness , height / 2),
                (-half_lenght+legs_thikness, -half_width +legs_thikness, height / 2)
            ]

            for i, pos in enumerate(leg_positions):
                bpy.ops.mesh.primitive_cube_add(size=1)
                leg = bpy.context.object
                leg.name = f"{name}_Leg_{i + 1}"
                leg.scale = (legs_thikness, legs_thikness, height)
                leg.parent = table_parent
                bpy.ops.object.transform_apply(scale=True)
                leg.location = pos
                if material:
                    MaterialFactory.apply_material(leg, material)

            return table_parent
