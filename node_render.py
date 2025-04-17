import json
import math
import os

import bpy

from ResourceFinder import get_finder
from furnitures_gen.furniture_factory import FurnitureFactory
from furnitures_gen.materials import MaterialFactory
from furnitures_gen.segment_factory import SegmentFactory


class NodeRender:
    @staticmethod
    def render_nodes(data,nodes_lookup):
        for node_dict in data["nodes"]:
            node_id = node_dict["id"]
            x = node_dict["x"]
            y = node_dict["y"]
            nodes_lookup[node_id] = (x, y)
            NodeRender.create_marker((x,y,0),node_id)

    @staticmethod
    def render_edges(data,nodes_lookup,house_parent):
        for edge in data["edges"]:
            NodeRender.create_wall_segment(
                edge_data=edge,
                nodes_lookup=nodes_lookup,
                parent_obj=house_parent
            )
            id_str = edge.get('id')
            output_path = os.path.abspath(f"blend_output\\{id_str}.blend")
            bpy.ops.wm.save_as_mainfile(filepath=output_path)
    @staticmethod
    def build_house_from_data(data):
        # Create an Empty to hold all walls
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
        house_parent = bpy.context.object
        house_parent.name = "HouseRoot"
        # Parse nodes into a dictionary for quick lookup
        nodes_lookup = {}
        NodeRender.render_nodes(data,nodes_lookup)

        # Create each wall from edges
        NodeRender.render_edges(data,nodes_lookup,house_parent)
        for furniture in data["furnitures"]:
            NodeRender.create_furniture(furniture,house_parent)

    @staticmethod
    def create_furniture(furniture, house_parent):
        furniture_type = furniture["type"]
        location = furniture["location"]
        orientation = furniture["orientation"]

        if furniture_type == "bed":
            FurnitureFactory.place_bed(location,orientation)
        if furniture_type == "table_set":
            FurnitureFactory.place_dinner_set(location,orientation)
        if furniture_type == "Bath":
            print("✅ Bath placement")
            FurnitureFactory.place_bath(location,orientation)
        if furniture_type == "Shower":
            print("✅ Shower placement")
            FurnitureFactory.place_shower(location, orientation)


    @staticmethod
    def load_floorplan_json(filepath):
        data = get_finder().load_json(filepath)
        return data

    @staticmethod
    def create_marker(location, name):
        bpy.ops.object.empty_add(type='SPHERE', radius=0.2, location=location)
        marker = bpy.context.object
        marker.name = name
    @staticmethod
    def build_from_data():
        # Example usage:
        filepath = "corrected_floorplan.json"
        #filepath = "experiment_floorplan.json"
        #filepath = "corrected_floorplan.json"
        floorplan_data = NodeRender.load_floorplan_json(filepath)
        NodeRender.build_house_from_data(floorplan_data)

    @staticmethod
    def create_wall_segment(edge_data, nodes_lookup, parent_obj):
        """
        Creates a 3D wall segment (a rectangular prism) from the center-line
        definition plus optional door/window openings.
        """
        start_node = edge_data["start_node"]
        end_node = edge_data["end_node"]

        # Retrieve the 2D coordinates of the nodes
        xA, yA = nodes_lookup[start_node]
        xB, yB = nodes_lookup[end_node]

        wall_type = edge_data.get("wall_type", "interior")
        stud_type = edge_data.get("stud_type", "2x4")
        wall_height = edge_data.get("height", 2.4)
        openings = edge_data.get("openings", [])
        name = edge_data.get("id", "N/A")

        dx = xB - xA
        dy = yB - yA
        wall_length = math.sqrt(dx * dx + dy * dy)
        mats = MaterialFactory.create_materials()
        SegmentFactory.create_wall_segment(
            parent=parent_obj,
            start_xy=(xA, yA),
            end_xy=(xB, yB),
            wall_height=wall_height,
            stud_spacing=0.4064,
            materials=mats,
            segment_name=f"{name}_Segment_",
            openings=openings,
            stud_type=stud_type
        )


