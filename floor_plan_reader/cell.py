class Cell:
    def __init__(self, x, y):
        self.is_stem = False
        self.is_root = False
        self.is_visited = False
        self.x = x
        self.y = y
        self.sprouted = False
        self.collided = False

    def __eq__(self, other):
        """Check equality based on x and y values."""
        if isinstance(other, Cell):
            return self.x == other.x and self.y == other.y
        return False

    def __hash__(self):
        """Generate a unique hash based on x and y values."""
        return hash((self.x, self.y))

    def __repr__(self):
        """String representation for debugging."""
        return f"Cell({self.x}, {self.y})"