import importlib
import os

import bpy
import math
from mathutils import Vector

from furnitures_gen import chair_factory, bed_factory
import table_factory
from furnitures_gen.bath_thub_factory import BathThubFactory
from furnitures_gen.bed_factory import BedFactory
from furnitures_gen.chair_factory import ChairFactory
from shower_factory import ShowerFactory
from table_factory import TableFactory

importlib.reload(table_factory)  # Force refresh
importlib.reload(chair_factory)
importlib.reload(bed_factory)

class FurnitureFactory:
    prototypes = {}
    prototype_collection = None
    furniture_collection = None

    def import_from_blend(blend_path, object_names):
        blend_abs_path = os.path.abspath(blend_path)
        object_dir = blend_abs_path + ""

        for obj_name in object_names:
            bpy.ops.wm.append(
                filepath=os.path.join(object_dir, obj_name),
                directory=object_dir,
                filename=obj_name
            )
            print(f"✅ Imported {obj_name} from {blend_path}")
    @staticmethod
    def create_furniture_collection():
        """Creates a dedicated collection for prototypes if it doesn't exist."""
        if "Furnitures" not in bpy.data.collections:
            FurnitureFactory.furniture_collection = bpy.data.collections.new("Furnitures")
            bpy.context.scene.collection.children.link(FurnitureFactory.furniture_collection)
        else:
            FurnitureFactory.furniture_collection = bpy.data.collections["Furnitures"]
    @staticmethod
    def create_prototype_collection():
        """Creates a dedicated collection for prototypes if it doesn't exist."""
        if "Prototypes" not in bpy.data.collections:
            FurnitureFactory.prototype_collection = bpy.data.collections.new("Prototypes")
            bpy.context.scene.collection.children.link(FurnitureFactory.prototype_collection)
        else:
            FurnitureFactory.prototype_collection = bpy.data.collections["Prototypes"]
    @staticmethod
    def register_furniture(name,obj):
        if FurnitureFactory.furniture_collection is None:
            FurnitureFactory.create_furniture_collection()

        FurnitureFactory.furniture_collection.objects.link(obj)
        bpy.context.collection.objects.unlink(obj)  # Remove from default scene collection
        for child in obj.children:
            FurnitureFactory.furniture_collection.objects.link(child)
            bpy.context.collection.objects.unlink(child)

        """Stores a prototype furniture object."""


    @staticmethod
    def register_prototype(name, obj):
        if FurnitureFactory.prototype_collection is None:
            FurnitureFactory.create_prototype_collection()

        FurnitureFactory.prototype_collection.objects.link(obj)
        bpy.context.collection.objects.unlink(obj)  # Remove from default scene collection
        for child in obj.children:
            FurnitureFactory.prototype_collection.objects.link(child)
            bpy.context.collection.objects.unlink(child)

        """Stores a prototype furniture object."""
        FurnitureFactory.prototypes[name] = obj

    @staticmethod
    def clone_prototype(parent=None,name="", location=(0,0,0), rotation=(0, 0, 0)):
        """Clones an existing prototype and places it at a new location."""
        if name not in FurnitureFactory.prototypes:
            raise ValueError(f"Prototype {name} not found!")

        original = FurnitureFactory.prototypes[name]
        new_obj = original.copy()
        #new_obj.data = original.data.copy()  # Ensure a separate data block
        new_obj.name = name

        # Clone children and maintain hierarchy
        for child in original.children:
            new_child = child.copy()
            new_child.data = child.data.copy()
            new_child.parent = new_obj
            #new_child.location += Vector(location)  # Adjust location relative to new parent
            bpy.context.collection.objects.link(new_child)
        new_obj.location = Vector(location)
        new_obj.rotation_euler = (
            math.radians(rotation[0]),
            math.radians(rotation[1]),
            math.radians(rotation[2])
        )
        bpy.context.collection.objects.link(new_obj)
        if parent is not None:
            new_obj.parent = parent

        FurnitureFactory.register_furniture(name, new_obj)
        return new_obj



    @staticmethod
    def create_furniture_prototypes():
        """Creates base furniture prototypes by importing from specific modules."""


        table = TableFactory.create_table("Prototype_Table")
        FurnitureFactory.register_prototype("Table", table)

        chair = ChairFactory.create_chair("Prototype_Chair")
        FurnitureFactory.register_prototype("Chair", chair)

        bed = BedFactory.create_bed("Prototype_Bed")
        FurnitureFactory.register_prototype("Bed", bed)

        bath = BathThubFactory.create_thub("Prototype_bath")
        FurnitureFactory.register_prototype("Bath", bath)

        shower = ShowerFactory.create_corner_shower("Prototype_Shower")
        FurnitureFactory.register_prototype("Shower", shower)

        print("✅ Furniture prototypes created.")

    @staticmethod
    def place_bed(location, rotation):
        FurnitureFactory.clone_prototype(name="Bed", location=location, rotation=rotation)
    @staticmethod
    def place_bath(location,rotation):
        FurnitureFactory.clone_prototype(name="Bath",location=location,rotation=rotation)
    @staticmethod
    def place_shower(location, rotation):
        FurnitureFactory.clone_prototype(name="Shower", location=location, rotation=rotation)

    @staticmethod
    def place_dinner_set(location, rotation):
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
        table_set = bpy.context.object
        table_set.name = "table_set"
        table_set.location = location
        table_set.rotation_euler = rotation
        FurnitureFactory.clone_prototype(parent=table_set, name="Table", location=(0, 0, 0))
        FurnitureFactory.clone_prototype(parent=table_set, name="Chair", location=(-0.34, -0.53, 0))
        FurnitureFactory.clone_prototype(parent=table_set, name="Chair", location=(0.34, -0.53, 0))
        FurnitureFactory.clone_prototype(parent=table_set, name="Chair", location=(-0.34, 0.53, 0), rotation=(0, 0, 180))
        FurnitureFactory.clone_prototype(parent=table_set, name="Chair", location=(0.34, 0.53, 0), rotation=(0, 0, 180))

    @staticmethod
    def place_furniture():
        """Places multiple furniture instances in the scene."""
        FurnitureFactory.clone_prototype(name="Table", location=(3, 3, 0))
        FurnitureFactory.clone_prototype(name="Chair", location=(3.5, 2.4, 0))
        FurnitureFactory.clone_prototype(name="Chair", location=(2.5, 2.4, 0))
        FurnitureFactory.clone_prototype(name="Chair", location=(3.5, 3.7, 0),rotation=(0,0,180))
        FurnitureFactory.clone_prototype(name="Chair", location=(2.5, 3.7, 0),rotation=(0,0,180))

        FurnitureFactory.clone_prototype(name="Bed", location=(13, 7, 0))

