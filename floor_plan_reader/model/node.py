class Node:
    def __init__(self,point):
        self.point = point
        self.lines=set()
        self.id = None
        self.pixel_per_meter = 15

    def get_x(self):
        return self.point[0]

    def get_y(self):
        return self.point[1]

    def get_json(self):
        return {"id": self.id, "x": self.get_x()/self.pixel_per_meter, "y": self.get_y()/self.pixel_per_meter}

    def __hash__(self):
        x = int(self.get_x()/2)
        y = int(self.get_y()/2)
        return hash((x, y))

    def __eq__(self, other):
        """Compare two vectors for equality based on their direction."""
        if isinstance(other, Node):
            return self.point == other.point
        return False
