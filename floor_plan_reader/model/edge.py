class Edge:
    def __init__(self, node_a, node_b, line):
        self.node_a = node_a
        self.node_b = node_b
        self.opening = set()
        self.line = line
        self.wall_height = 2.7432
        self.stud_type = "2x6"

    def copy(self):
        e = Edge(self.node_a, self.node_b, self.line)
        for o in self.line.seg.openings:
            e.opening.add(o.copy())
        return e

    def convert_to_scale(self, meter_per_pixel):
        if len(self.line.seg.parts) > 1:
            self.line.seg.calculate_openings()
        e = self.copy()
        openings = []
        for o in e.opening:
            o_d = o.convert_to_scale(meter_per_pixel)
            openings.append(o_d)
        e.opening = set()
        for o in openings:
            e.opening.add(o)
        return e

    def get_json(self):
        if len(self.line.seg.parts) > 1:
            self.line.seg.calculate_openings()
        str_value = {"id": f"Ext_{self.node_a.id}_{self.node_b.id}",
                     "start_node": self.node_a.id, "end_node": self.node_b.id,
                     "wall_type": "exterior",
                     "stud_type": self.stud_type,
                     "height": self.wall_height,
                     "openings": [opening.to_json() for opening in self.line.seg.openings]
                     }
        return str_value

    def getHash(self):
        return hash((self.node_a.point, self.node_b.point))

    def __hash__(self):
        return self.getHash()

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()
