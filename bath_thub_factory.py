import bpy
import math

class BathThubFactory:

    @staticmethod
    def create_thub():
        # Delete default objects
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)

        # Create the main tub shape
        bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=2, depth=1, location=(0, 0, 0.5))
        tub = bpy.context.object
        tub.name = "Bathtub"

        # Scale the tub to make it oval
        bpy.ops.transform.resize(value=(1.5, 1, 1))

        # Create the inner cutout
        bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=1.8, depth=1.1, location=(0, 0, 0.55))
        inner_tub = bpy.context.object
        inner_tub.name = "InnerTub"

        # Scale the inner cutout to match the oval shape
        bpy.ops.transform.resize(value=(1.4, 0.9, 1))

        # Use the Boolean modifier to cut out the inner part
        bool_mod = tub.modifiers.new(name="BoolCut", type='BOOLEAN')
        bool_mod.object = inner_tub
        bool_mod.operation = 'DIFFERENCE'
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)

        # Delete the inner cutout object
        bpy.ops.object.select_all(action='DESELECT')
        inner_tub.select_set(True)
        bpy.ops.object.delete()

        # Add a smooth modifier to the tub
        smooth_mod = tub.modifiers.new(name="Smooth", type='SMOOTH')
        smooth_mod.iterations = 10
        bpy.ops.object.modifier_apply(modifier=smooth_mod.name)

        # Add a subsurf modifier for smoother edges
        subsurf_mod = tub.modifiers.new(name="Subsurf", type='SUBSURF')
        subsurf_mod.levels = 2
        bpy.ops.object.modifier_apply(modifier=subsurf_mod.name)

        # Create the faucet
        bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.1, depth=0.5, location=(1.5, 0, 1.2))
        faucet = bpy.context.object
        faucet.name = "Faucet"

        # Add a sphere to the top of the faucet
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.15, location=(1.5, 0, 1.45))
        faucet_top = bpy.context.object
        faucet_top.name = "FaucetTop"

        # Join the faucet parts
        bpy.ops.object.select_all(action='DESELECT')
        faucet.select_set(True)
        faucet_top.select_set(True)
        bpy.context.view_layer.objects.active = faucet
        bpy.ops.object.join()

        # Move the bathtub to the origin
        bpy.ops.object.select_all(action='DESELECT')
        tub.select_set(True)
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
        bpy.ops.object.location_clear()

        # Set shading to smooth
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.shade_smooth()

        print("Bathtub created successfully!")