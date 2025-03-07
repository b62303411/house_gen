import bpy
class CutoutUtil:
    @staticmethod
    def cuttout_util(cutout_obj, object):
        objects = []
        if isinstance(object, bpy.types.Collection):
            objects = [obj for obj in object.objects if obj.type == 'MESH']
        elif isinstance(object, bpy.types.Object) and object.type == 'MESH':
            objects.append(object)
        elif isinstance(object, bpy.types.Object):
            objects = [child for child in object.children if child.type == 'MESH']

        name_prefix="dontcare"
        # Apply Boolean difference for each wall mesh
        success = False
        for obj in objects:
            if obj.type == 'MESH' and obj.data and len(obj.data.polygons) > 0:
                bool_mod = obj.modifiers.new(name=f"{name_prefix}_Cut", type='BOOLEAN')
                bool_mod.object = cutout_obj
                bool_mod.operation = 'DIFFERENCE'

                bpy.context.view_layer.objects.active = obj
                bpy.ops.object.modifier_apply(modifier=bool_mod.name)
                success = True
                print(f"✅ Applied opening cut to {obj.name}")