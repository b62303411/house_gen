class Node:
    def __init__(self,point):
        self.point = point
        self.lines=set()
        self.id = None

    def get_x(self):
        return self.point[0]

    def get_y(self):
        return self.point[1]

    def get_json(self):
        return {"id": self.id, "x": self.get_x()/15, "y": self.get_y()/15}

    def getHash(self):
        x = int(self.get_x())
        y = int(self.get_y())
        return hash((x,y))

    def __hash__(self):
        x = int(self.get_x())
        y = int(self.get_y())
        return hash((x, y))

    def __eq__(self, other):
        """Compare two vectors for equality based on their direction."""
        if isinstance(other, Node):
            return self.point == other.point
        return False
