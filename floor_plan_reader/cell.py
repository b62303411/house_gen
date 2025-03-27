from numpy import int64


class Cell:
    def __init__(self, x : int, y : int):
        self.is_stem = False
        self.is_root = False
        self.is_visited = False
        self.x = int(x)
        self.y = int(y)
        self.sprouted = False
        self.collided = False

    @property
    def x(self) -> int:
        return self._x

    @x.setter
    def x(self, value: int) -> None:
        if not isinstance(value, int64) and not isinstance(value,int):
            raise TypeError("`x` must be a int.")
        self._x = value

    @property
    def y(self) -> int:
        return self._y

    @x.setter
    def y(self, value: int) -> None:
        if not isinstance(value, int64) and not isinstance(value,int):
            raise TypeError("`name` must be a string.")
        self._y = value
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