import math


class Vector:

    def __init__(self, direction):
        self.direction = direction
        self.length = 1

    def copy(self):
        return Vector(self.direction)

    def __hash__(self):
        """Hash the vector based on its direction."""
        return hash(self.direction)

    def __eq__(self, other):
        """Compare two vectors for equality based on their direction."""
        if isinstance(other, Vector):
            return self.direction == other.direction
        return False

    def __repr__(self):
        """String representation of the vector."""
        return f"Vector(direction={self.direction}, length={self.length})"

    def calculate_length(self):
        """Calculate the length (magnitude) of the vector."""
        return math.sqrt(self.direction[0] ** 2 + self.direction[1] ** 2)

    def get_normal(self):
        """Get the normal (perpendicular) vector."""
        direction = self.direction
        length = math.hypot(direction[0], direction[1])
        if length == 0:
            return None

        #nx /= length  # Make it unit length
        #ny /= length
        return Vector((-direction[1], direction[0]))

    def normalize(self):
        """Normalize the vector to have a length of 1."""
        if self.length == 0:
            raise ValueError("Cannot normalize a vector with zero length.")
        self.direction = (self.direction[0] / self.length, self.direction[1] / self.length)
        self.length = 1

    def scale(self, scalar):
        """Scale the vector by a scalar."""
        self.direction = (self.direction[0] * scalar, self.direction[1] * scalar)
        self.length = 1

    def dot_product(self, other):
        """Calculate the dot product with another vector."""
        return self.direction[0] * other.direction[0] + self.direction[1] * other.direction[1]

    def angle_between(self, other):
        """Calculate the angle between this vector and another vector in radians."""
        dot_product = self.dot_product(other)
        magnitude_product = self.length * other.length
        if magnitude_product == 0:
            raise ValueError("Cannot calculate angle with a zero-length vector.")
        return math.acos(dot_product / magnitude_product)

    def opposite(self):
        """Return a new vector in the opposite direction without modifying the original."""
        return Vector((-self.direction[0], -self.direction[1]))
    def dx(self):
        return self.direction[0]

    def dy(self):
        return self.direction[1]

    def __add__(self, other):
        """Add another vector to this vector."""
        return Vector((self.direction[0] + other.direction[0], self.direction[1] + other.direction[1]))

    def __sub__(self, other):
        """Subtract another vector from this vector."""
        return Vector((self.direction[0] - other.direction[0], self.direction[1] - other.direction[1]))

    def __mul__(self, scalar):
        """Multiply the vector by a scalar."""
        return Vector((self.direction[0] * scalar, self.direction[1] * scalar))

    def __truediv__(self, scalar):
        """Divide the vector by a scalar."""
        if scalar == 0:
            raise ValueError("Cannot divide by zero.")
        return Vector((self.direction[0] / scalar, self.direction[1] / scalar))

    def __repr__(self):
        """String representation of the vector."""
        return f"Vector(direction={self.direction}, length={self.length})"

    @staticmethod
    def project(point, origin, direction):
        """
        Projects the vector (point - origin) onto 'direction' (assumed unit).
        Returns a scalar distance (float).
        """
        vx = point[0] - origin[0]
        vy = point[1] - origin[1]
        # Dot product with the direction (dx, dy)
        return vx * direction.dx() + vy * direction.dy()