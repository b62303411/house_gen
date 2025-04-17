class DataPoint:
    def __init__(self, steps, min_x, min_y, max_x, max_y,k):
        self.steps = steps
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max_x
        self.max_y = max_y
        self.extra = None
        self.k=k
    def get_magnitude(self):
        return self.steps

    def get_normal(self):
        return self.k.direction.get_normal()
    def get_center(self):
        if self.min_y is None or self.max_x is None:
            return 0,0
        center_x = (self.min_x + self.max_x) / 2.0
        center_y = (self.min_y + self.max_y) / 2.0
        return center_x, center_y

    def __lt__(self, other):
        """Define how to compare two Vector objects for sorting."""
        return self.steps < other.steps
    def direction(self):
        return self.k.direction