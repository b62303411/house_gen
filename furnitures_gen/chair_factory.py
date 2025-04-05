import bpy

from materials import MaterialFactory

class ChairFactory:
    @staticmethod
    def create_chair(name="Chair", seat_size=0.5, seat_height=0.45, back_height=0.9,legs_thikness=0.07, material=None, location=(0, 0, 0)):
        """Creates a simple chair with a seat, four legs, and a backrest using a parent-child hierarchy."""

        # Create an empty object as the parent
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=location)
        chair_parent = bpy.context.object
        chair_parent.name = name

        # Seat
        bpy.ops.mesh.primitive_cube_add(size=1)
        seat = bpy.context.object
        seat.name = f"{name}_Seat"
        seat.scale = (seat_size , seat_size , 0.05)
        seat.parent = chair_parent
        bpy.ops.object.transform_apply(scale=True)
        seat.location =(0,0,seat_height)
        if material:
            MaterialFactory.apply_material(seat, material)


        half_seat_size = seat_size / 2
        # Legs
        leg_positions = [
            (half_seat_size  - legs_thikness, half_seat_size - legs_thikness, half_seat_size),
            (-half_seat_size + legs_thikness, half_seat_size - legs_thikness, half_seat_size),
            (half_seat_size - legs_thikness, -half_seat_size + legs_thikness, half_seat_size),
            (-half_seat_size + legs_thikness, -half_seat_size + legs_thikness, half_seat_size)
        ]

        for i, pos in enumerate(leg_positions):
            bpy.ops.mesh.primitive_cube_add(size=1)
            leg = bpy.context.object
            leg.name = f"{name}_Leg_{i + 1}"
            leg.scale = (legs_thikness, legs_thikness, seat_height)
            leg.parent = chair_parent
            bpy.ops.object.transform_apply(scale=True)
            leg.location = pos
            if material:
                MaterialFactory.apply_material(leg, material)


        # Backrest
        bpy.ops.mesh.primitive_cube_add(size=1)
        backrest = bpy.context.object
        backrest.name = f"{name}_Backrest"
        backrest.scale = (seat_size / 2, 0.05, back_height / 2)
        backrest.parent = chair_parent
        bpy.ops.object.transform_apply(scale=True)
        backrest.location = (0,  - seat_size / 2 + 0.05, seat_height / 2 + back_height / 2)

        if material:
            MaterialFactory.apply_material(backrest, material)

        return chair_parent
