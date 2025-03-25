class Line:
    def __init__(self, start_point,end_point,id,seg,geometry):
        self.start_point = start_point
        self.end_point = end_point
        self.id= id
        self.seg = seg
        self.geometry=geometry

    def __hash__(self):
        return hash((self.start_point, self.end_point))

    def __eq__(self, other):
        """Compare two vectors for equality based on their direction."""
        if isinstance(other, Line):
            return self.start_point == other.start_point and self.end_point==other.end_point
        return False