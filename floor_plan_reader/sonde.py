class Sonde:
    def __init__(self, direction, data):
        self.direction = direction
        if data is None:
            pass
        self.data = data
        self.min = 500
        self.max = 0

    def get_center(self):
        return self.data.get_center()

    def get_magnitude(self):
        return self.data.steps

    def __lt__(self, other):
        """Define how to compare two Vector objects for sorting."""
        if self.data is None:
            return True
        return self.data.steps < other.data.steps
