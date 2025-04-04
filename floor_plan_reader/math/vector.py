import math


class Vector:

    def __init__(self, direction):
        self.direction = direction
        self.length = 1

    @staticmethod
    def make_from(other):
        return Vector(other.direction)

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
        return self

    def scale(self, scalar):
        """Scale the vector by a scalar."""
        self.direction = (self.direction[0] * scalar, self.direction[1] * scalar)
        self.length = 1

    def dot_product(self, other):
        """Calculate the dot product with another vector."""
        return self.direction[0] * other.direction[0] + self.direction[1] * other.direction[1]

    def distance(self,other):
        dx = self.direction[0] - other.direction[0]
        dy = self.direction[1] - other.direction[1]
        return math.sqrt(dx**2+dy**2)
    def angle_between(self, other):
        """Calculate the angle between this vector and another vector in radians."""
        dot_product = self.dot_product(other)
        magnitude_product = self.length * other.length
        if magnitude_product == 0:
            raise ValueError("Cannot calculate angle with a zero-length vector.")
        return math.acos(dot_product / magnitude_product)
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



    def opposite(self):
        """Return a new vector in the opposite direction without modifying the original."""
        return Vector((-self.direction[0], -self.direction[1]))
    def dx(self):
        return self.direction[0]

    def dy(self):
        return self.direction[1]

    def distance_to_line(self, point, line_point):
        """
        Calculate the perpendicular distance from a point to an infinite line.
        Handles zero-length vectors by returning point-to-point distance.
        """
        # Handle zero-length vector case
        if self.calculate_length() == 0:
            return math.hypot(point[0] - line_point[0],
                              point[1] - line_point[1])

        # Get normal vector
        normal = self.get_normal()
        if normal is None:
            return math.hypot(point[0] - line_point[0],
                              point[1] - line_point[1])

        # Normalize the normal vector
        normal_length = normal.calculate_length()
        if normal_length == 0:
            return math.hypot(point[0] - line_point[0],
                              point[1] - line_point[1])

        normal.direction = (normal.direction[0] / normal_length,
                            normal.direction[1] / normal_length)

        # Vector from line_point to our point
        vx = point[0] - line_point[0]
        vy = point[1] - line_point[1]

        # Project onto normal gives perpendicular distance
        return abs(vx * normal.direction[0] + vy * normal.direction[1])
    def distance_from_point_on_normal(self, point):
        point = Vector((point.x,point.y))
        """
        Computes the perpendicular distance from a given `point` (Vector)
        to the line passing through `self` in the direction of this vector.

        This uses projection onto the normal of the vector's direction.
        """
        # Step 1: Get the normal of this vector
        normal = self.get_normal()
        if normal is None:
            raise ValueError("Cannot compute normal for zero-length vector.")

        # Step 2: Normalize the normal vector
        normal.length = normal.calculate_length()
        normal.normalize()

        # Step 3: Vector from self to point
        to_point = point - self

        # Step 4: Project onto the normal and return the absolute value
        return abs(to_point.dot_product(normal))

    def distance_to_line_segment(self, point, segment_start, segment_end):
        pass


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