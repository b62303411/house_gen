import json
import math

import bpy

from materials import MaterialFactory
from segment_factory import SegmentFactory


class NodeRender:

    def build_house_from_data(data):
        # Create an Empty to hold all walls
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
        house_parent = bpy.context.object
        house_parent.name = "HouseRoot"
        # Parse nodes into a dictionary for quick lookup
        nodes_lookup = {}
        for node_dict in data["nodes"]:
            node_id = node_dict["id"]
            x = node_dict["x"]
            y = node_dict["y"]
            nodes_lookup[node_id] = (x, y)

        # Create each wall from edges
        for edge in data["edges"]:
            NodeRender.create_wall_segment(
                edge_data=edge,
                nodes_lookup=nodes_lookup,
                parent_obj=house_parent
            )

    def load_floorplan_json(filepath):
        """Load the floor plan data (nodes, edges) from a JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return data

    @staticmethod
    def build_from_data():
        # Example usage:
        filepath = "E:/workspace/blender_house/house_gen/house_test.json"
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


