class Node:
    def __init__(self, point):
        self.point = point
        self.lines = set()
        self.id = None
        self.pixel_per_meter = 15

    def get_x(self):
        return self.point[0]

    def get_y(self):
        return self.point[1]

    def copy(self):
        n = Node(self.point)
        n.id = self.id
        n.lines = self.lines
        return n

    def convert_to_scale(self, meter_per_pixel):
        n = self.copy()
        (x, y) = n.point
        n.point = (x * meter_per_pixel, y * meter_per_pixel)
        return n

    def get_json(self):
        return {"id": self.id, "x": self.get_x(), "y": self.get_y()}

    def __hash__(self):
        x = int(self.get_x() / 3)
        y = int(self.get_y() / 3)
        return hash((x, y))

    def __eq__(self, other):
        if not isinstance(other, Node):
            return False
        return abs(self.get_x() - other.get_x()) < 3 and abs(self.get_y() - other.get_y()) < 3
