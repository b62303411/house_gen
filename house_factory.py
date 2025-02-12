import importlib
import math

import bpy

import frame_factory
import furniture_factory
import segment_factory

from furniture_factory import FurnitureFactory
from materials import MaterialFactory
from segment_factory import SegmentFactory

importlib.reload(furniture_factory)
importlib.reload(frame_factory)
importlib.reload(segment_factory)

class WallNode:
    def __init__(self, node_id, x, y):
        self.id = node_id
        self.x = x
        self.y = y
        self.edges = []  # list of WallEdge objects that connect here

class WallEdge:
    def __init__(self, edge_id, node_a, node_b, door_specs=None):
        self.id = edge_id
        self.node_a = node_a  # references a WallNode
        self.node_b = node_b
        self.door_specs = door_specs if door_specs else []
        # Possibly store wall thickness, materials, etc. on the edge if needed.

class InteriorWallGraph:
    def __init__(self):
        self.nodes = {}  # dict of node_id -> WallNode
        self.edges = {}  # dict of edge_id -> WallEdge

    def add_node(self, node_id, x, y):
        node = WallNode(node_id, x, y)
        self.nodes[node_id] = node
        return node

    def add_edge(self, edge_id, node_a, node_b, door_specs=None):
        edge = WallEdge(edge_id, node_a, node_b, door_specs)
        self.edges[edge_id] = edge
        node_a.edges.append(edge)
        node_b.edges.append(edge)
        return edge
class HouseFactory:
    # Updated House Size (~3000 sq ft)
    HOUSE_GRID_WIDTH = 50  # 50ft wide
    HOUSE_GRID_LENGTH = 60  # 60ft long
    GRID_SIZE = 0.3048  # 1ft in meters
    HOUSE_HEIGHT = 2.7  # 2.7m (~9ft) wall height
    # Create materials
    materials = MaterialFactory.create_materials()

    # Define South-facing Windows (for Passive Solar Heating)
    SOUTH_WALL_WINDOWS = [
        {"center_x": -20 * GRID_SIZE, "bottom_z": 0.5, "width": 1.5, "height": 2},
        {"center_x": 0 * GRID_SIZE, "bottom_z": 0.5, "width": 1.5, "height": 2},
        {"center_x": 20 * GRID_SIZE, "bottom_z": 0.5, "width": 1.5, "height": 2}
    ]

    @staticmethod
    def create_prototypes():
        FurnitureFactory.create_furniture_prototypes()

    @staticmethod
    def create_furniture():
        FurnitureFactory.create_furniture_prototypes()
        FurnitureFactory.place_furniture()

    @staticmethod
    def create_inner_wall(name,footprint_points, wall_height, stud_spacing, materials,doors_spec):
        # 1) Créer l'objet parent principal
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
        wall_parent = bpy.context.object
        wall_parent.name = name
        num_points = len(footprint_points)
        for i in range(num_points):
            x0, y0 = footprint_points[i]
            x1, y1 = footprint_points[(i + 1) % num_points]  # point suivant (boucle)
            # Example logic: let even segments overlap by 0.2 m at the 'end',
            # odd segments overlap by 0.2 m at the 'start'.
            # (In reality, decide interior vs. exterior corners or whichever logic you want.)
            #door = doors_spec[i]
            # Appel à create_wall_segment(...)
            # => construit le segment entre (x0, y0) et (x1, y1)
            SegmentFactory.create_wall_segment(
                parent=wall_parent,
                start_xy=(x0, y0),
                end_xy=(x1, y1),
                wall_height=wall_height,
                stud_spacing=stud_spacing,
                materials=materials,
                segment_name=f"{name}_Segment_{i + 1}",
                #doors_specs=door,
                stud_type="2x4"
            )


    @staticmethod
    def create_outer_wall(name, footprint_points, wall_height, stud_spacing, materials, windows_spec):
        """
        Construit un mur externe formé de plusieurs segments (une boucle).
        Chaque paire consécutive de points (i -> i+1) définit un mur droit.
        Ensuite, on place un assemblage de coin (4 montants) à chaque sommet.
        """
        # 1) Créer l'objet parent principal
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
        outer_wall_parent = bpy.context.object
        outer_wall_parent.name = name

        # Create a plane mesh
        bpy.ops.mesh.primitive_plane_add(size=1, enter_editmode=False, align='WORLD', location=(0, 0, 0))

        num_points = len(footprint_points)
        x0, y0 = footprint_points[0]
        x1, y1 = footprint_points[2]
        width = abs(y1-y0)
        lenght = abs(x0-x1)
        obj = bpy.context.object
        obj.name = "floor"
        obj.scale = (lenght ,width ,0)
        obj.parent = outer_wall_parent

        # 2) Construire chaque segment de mur
        for i in range(num_points):
            x0, y0 = footprint_points[i]
            x1, y1 = footprint_points[(i + 1) % num_points]  # point suivant (boucle)
            # Example logic: let even segments overlap by 0.2 m at the 'end',
            # odd segments overlap by 0.2 m at the 'start'.
            # (In reality, decide interior vs. exterior corners or whichever logic you want.)
            window_spec = windows_spec[i]
            # Appel à create_wall_segment(...)
            # => construit le segment entre (x0, y0) et (x1, y1)
            SegmentFactory.create_wall_segment(
                parent=outer_wall_parent,
                start_xy=(x0, y0),
                end_xy=(x1, y1),
                wall_height=wall_height,
                stud_spacing=stud_spacing,
                materials=materials,
                segment_name=f"{name}_Segment_{i + 1}",
                window_specs=window_spec
            )