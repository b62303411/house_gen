import math


class CollisionBox:
    def __init__(self, center_x, center_y, width, length, rotation):
        self.center_x = center_x
        self.center_y = center_y
        self.width = width
        self.length = length
        self.rotation = rotation
        self.default_direction = (1,0)
        self.corners = None

    def get_area(self):
        return self.width*self.length
    def get_direction(self):
        """
        Convert a rotation angle to a direction vector, assuming default direction is (1,0).

        Args:
            rotation_angle (float): Angle in degrees

        Returns:
            tuple: Normalized direction vector as (dx, dy)
        """
        # Convert angle to radians
        angle_rad = math.radians(self.rotation)

        # Calculate direction vector components
        dx = math.cos(angle_rad)
        dy = math.sin(angle_rad)

        # For grid movement, we need integer directions
        # Round to nearest integer: 0, 1, or -1
        if abs(dx) > abs(dy):
            # Horizontal movement dominates
            return (int(round(dx)), 0)
        else:
            # Vertical movement dominates
            return (0, int(round(dy)))

    def get_center(self):
        return self.center_x, self.center_y


    def area_of_triangle(self, A, B, C):
        return abs((A[0]*(B[1]-C[1]) + B[0]*(C[1]-A[1]) + C[0]*(A[1]-B[1])) / 2.0)

    def is_point_inside(self, x, y):
        corners = self.calculate_corners()
        A, B, C, D = corners
        P = (x, y)

        rect_area = self.area_of_triangle(A, B, C) + self.area_of_triangle(A, C, D)
        area_sum = (
            self.area_of_triangle(P, A, B) +
            self.area_of_triangle(P, B, C) +
            self.area_of_triangle(P, C, D) +
            self.area_of_triangle(P, D, A)
        )

        return abs(rect_area - area_sum) < 1e-5

    def derive_direction_and_normal(self):
        angle_rad = math.radians(self.rotation)

        # Direction vector (rotated from default direction (1,0))
        direction = (math.cos(angle_rad), math.sin(angle_rad))

        # Normal vector (rotated 90 degrees from direction)
        normal = (-direction[1], direction[0])

        return direction, normal
    def calculate_corners(self):
        if self.corners is not None:
            return self.corners
        """Get OBB corner points in world coordinates"""
        half_length = (self.length) / 2 -.5
        half_width = (self.width) / 2 -.5
        direction,normal= self.derive_direction_and_normal()

        dir_vec = (direction[0] * half_length, direction[1] * half_length)
        norm_vec = (normal[0] * half_width, normal[1] * half_width)

        # Calculate corners without offsets
        top_left = (
            self.center_x - dir_vec[0] - norm_vec[0],
            self.center_y - dir_vec[1] + norm_vec[1]  # Y-down adjustment
        )
        bottom_right = (
            self.center_x + dir_vec[0] + norm_vec[0],
            self.center_y + dir_vec[1] - norm_vec[1]  # Y-down adjustment
        )

        # Other corners for completeness
        top_right = (
            self.center_x + dir_vec[0] - norm_vec[0],
            self.center_y + dir_vec[1] + norm_vec[1]
        )
        bottom_left = (
            self.center_x - dir_vec[0] + norm_vec[0],
            self.center_y - dir_vec[1] - norm_vec[1]
        )

        # Order: [top-left, bottom-left, top-right, bottom-right]
        corners = [top_left, top_right, bottom_right, bottom_left]

        # Apply pixel alignment (rounding) once at the end
        self.corners =[(int(round(x)), int(round(y))) for x, y in corners]

        return self.corners
