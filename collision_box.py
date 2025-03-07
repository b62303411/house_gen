import math


class CollisionBox:
    def __init__(self, center_x, center_y, width, length, rotation):
        self.center_x = center_x
        self.center_y = center_y
        self.width = width
        self.length = length
        self.rotation = rotation
        self.default_direction = (1,0)

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


    def collidepoint(self, x, y):
            """Check if a given point (x,y) is inside the rotated rectangle."""
            corners = self.calculate_corners()

            def cross(ax, ay, bx, by):
                return ax * by - ay * bx

            inside = True
            for i in range(4):
                corner_a = corners[i]
                corner_b = corners[(i + 1) % 4]
                edge_x, edge_y = corner_b[0] - corner_a[0], corner_b[1] - corner_a[1]
                point_x, point_y = x - corner_a[0], y - corner_a[1]

                if edge_x * point_y - edge_y * point_x < 0:
                    inside = False
                    break

            return inside

    def derive_direction_and_normal(self):
        angle_rad = math.radians(self.rotation)

        # Direction vector (rotated from default direction (1,0))
        direction = (math.cos(angle_rad), math.sin(angle_rad))

        # Normal vector (rotated 90 degrees from direction)
        normal = (-direction[1], direction[0])

        return direction, normal
    def calculate_corners(self):
        """Get OBB corner points in world coordinates"""
        half_length = self.length / 2
        half_width = self.width / 2
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
        c =[(int(round(x)), int(round(y))) for x, y in corners]

        return c
