import logging
from itertools import count

from floor_plan_reader.model.edge import Edge
from floor_plan_reader.model.node import Node


class Model:
    def __init__(self):
        self.nodes = {}
        self.edges = {}
        self.node_seq = count(start=1)

    def add_node(self, node):
        self.nodes[node.__hash__()] = node

    def add_edges(self,edge):
        self.edges[edge.__hash__()] = edge

    def convert_to_scale(self, meter_per_pixel):
        m = Model()
        for e in self.edges.values():
            copy_e = e.convert_to_scale(meter_per_pixel)
            m.add_edges(copy_e)
        for n in self.nodes.values():
            copy_n = n.convert_to_scale(meter_per_pixel)
            m.add_node(copy_n)
        return m

    def create_node(self, position):
        x = position[0]
        y = position[1]
        n = Node((x, y))
        hash_ = n.__hash__()
        if hash_ in self.nodes.keys():
            return self.nodes.get(hash_)
        else:
            n = Node((x, y))
            n.id = f"N{next(self.node_seq)}"
            self.add_node(n)
            return n

    def get_edges(self):
        return self.edges.values()

    def get_nodes(self):
        return self.nodes.values()

    def has_node(self, node):
        return node.__hash__() in self.nodes.keys()

    def create_edge(self, node_a, node_b, line):
        if node_a is None or node_b is None:
            logging.error("node error")
            return
        e = Edge(node_a, node_b, line)
        if e.__hash__() in self.edges.keys():
            return self.edges.get(e.__hash__())
        else:
            self.add_edges(e)
            return e

