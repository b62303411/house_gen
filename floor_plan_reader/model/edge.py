class Edge:
    def __init__(self, node_a, node_b, line):
        self.node_a = node_a
        self.node_b = node_b
        self.line = line
        self.wall_height = 2.7432
        self.stud_type = "2x6"

    def get_json(self):
        str_value = {"id": f"Ext_{self.node_a.id}_{self.node_b.id}",
                     "start_node": self.node_a.id, "end_node": self.node_b.id,
                     "wall_type": "exterior",
                     "stud_type": self.stud_type,
                     "height": self.wall_height}
        return str_value

    def getHash(self):
        return hash((self.node_a.point, self.node_b.point))

    def __hash__(self):
        return self.getHash()
