import math


class CollisionBox:
    def __init__(self, center_x, center_y, width, length, rotation):
        self.center_x = center_x
        self.center_y = center_y
        self.width = width
        self.length = length
        self.rotation = rotation
        self.default_direction = (1, 0)
        self.corners = None

    def __eq__(self, other):
        if not isinstance(other, CollisionBox):
            return False
        return (self.center_x, self.center_y, self.width, self.length, self.rotation) == \
               (other.center_x, other.center_y, other.width, other.length, other.rotation)

    def __hash__(self):
        return hash((self.center_x, self.center_y, self.width, self.length, self.rotation))

    def get_area(self):
        return self.width * self.length

    def get_direction(self):
        angle_deg = round(self.rotation / 45.0) * 45 % 360
        directions = {
            0: (1, 0),
            45: (math.sqrt(2) / 2, math.sqrt(2) / 2),
            90: (0, 1),
            135: (-math.sqrt(2) / 2, math.sqrt(2) / 2),
            180: (-1, 0),
            225: (-math.sqrt(2) / 2, -math.sqrt(2) / 2),
            270: (0, -1),
            315: (math.sqrt(2) / 2, -math.sqrt(2) / 2)
        }
        return directions.get(angle_deg, (0, 0))

    def get_vector(self):
        dir = self.get_direction()
        vector = dir * self.length
        return vector

    def get_center(self):
        return self.center_x, self.center_y

    def area_of_triangle(self, A, B, C):
        return abs((A[0] * (B[1] - C[1]) + B[0] * (C[1] - A[1]) + C[0] * (A[1] - B[1])) / 2.0)

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

    def is_on_same_axis_as(self, other, tolerance=1e-5):
        """
        Check that 'self' and 'other' both:
          1) Have the same orientation (differ by 0° or 180°)
          2) Are collinear along that orientation (their centers differ only along the direction)

        Returns:
            bool: True if they are on the same axis, False otherwise.
        """
        # 1) Check if they're parallel (0 or 180 difference)
        angle_diff = abs((self.rotation - other.rotation) % 180)
        if angle_diff > tolerance and abs(angle_diff - 180) > tolerance:
            return False  # Not parallel => can't be on same axis

        # 2) Ensure center offsets do NOT differ along the normal
        #    If they're truly on the same axis, the vector from self.center to other.center
        #    should align with self's direction, meaning no (or negligible) projection on self's normal.

        # Get self's direction & normal (unit or not, doesn't matter for ratio checks)
        direction, normal = self.derive_direction_and_normal()
        # Vector from self center to other center
        dx = other.center_x - self.center_x
        dy = other.center_y - self.center_y

        # Dot that vector with the normal. If near 0, they're aligned along direction
        dot_with_normal = dx * normal[0] + dy * normal[1]
        if abs(dot_with_normal) > tolerance:
            return False  # There's too much offset along the normal => not collinear

        return True
    def get_normal_trace_points(self, steps=500, step_size=1.0):
        """
        Generate two series of points along the box's normal axis, starting from the center
        and extending outward in both directions.

        Args:
            steps (int): How many steps to take in each direction from the center.
            step_size (float): Distance between each step.

        Returns:
            (List[Tuple[float, float]], List[Tuple[float, float]]):
                A tuple of (left_side_points, right_side_points), each containing points outward
                along negative/positive normal directions.
        """
        # 1) Get and normalize the normal
        nx, ny = self.get_normal()
        length = math.hypot(nx, ny)
        if length == 0:
            return [], []

        nx /= length  # Make it unit length
        ny /= length

        cx, cy = self.get_center()

        # 2) Create lists for each direction
        left_side_points = []
        right_side_points = []

        # 3) Negative normal (e.g. 'left')
        for i in range(1, steps + 1):
            px = cx - nx * step_size * i
            py = cy - ny * step_size * i
            left_side_points.append((px, py))

        # 4) Positive normal (e.g. 'right')
        for i in range(1, steps + 1):
            px = cx + nx * step_size * i
            py = cy + ny * step_size * i
            right_side_points.append((px, py))

        return left_side_points, right_side_points
    def derive_direction_and_normal(self):
        angle_rad = math.radians(self.rotation)

        # Direction vector (rotated from default direction (1,0))
        direction = (math.cos(angle_rad), math.sin(angle_rad))

        # Normal vector (rotated 90 degrees from direction)
        normal = (-direction[1], direction[0])

        return direction, normal

    def is_parallel_to(self, other, tolerance=1e-5):
        angle_diff = abs(self.rotation - other.rotation) % 180
        return angle_diff < tolerance or abs(angle_diff - 180) < tolerance

    def is_overlapping(self, other):
        return other.is_point_inside(self.center_x, self.center_y)

    def get_ray_trace_points(self):
        direction = self.get_direction()
        half_length = self.length / 2.0
        points = []
        for factor in [0.25, 0.5, 0.75]:
            point_x = self.center_x + direction[0] * half_length * factor
            point_y = self.center_y + direction[1] * half_length * factor
            points.append((point_x, point_y))
        return points

    def get_normal(self):
        direction = self.get_direction()
        return (-direction[1], direction[0])

    def get_extended_ray_trace_points(self, max_x, max_y):
        direction = self.get_direction()
        half_length = self.length / 2.0

        points_forward = []
        points_backward = []
        # Start points just outside the rectangle at both ends
        start_forward_x = self.center_x + direction[0] * half_length
        start_forward_y = self.center_y + direction[1] * half_length
        start_backward_x = self.center_x - direction[0] * half_length
        start_backward_y = self.center_y - direction[1] * half_length

        # Forward iteration
        current_x, current_y = start_forward_x + direction[0], start_forward_y + direction[1]
        while 0 <= current_x <= max_x and 0 <= current_y <= max_y:
            points_forward.append((current_x, current_y))
            current_x += direction[0]
            current_y += direction[1]

        # Backward iteration
        current_x, current_y = start_backward_x - direction[0], start_backward_y - direction[1]
        while 0 <= current_x <= max_x and 0 <= current_y <= max_y:
            points_backward.append((current_x, current_y))
            current_x -= direction[0]
            current_y -= direction[1]

        return points_forward, points_backward

    def set_position(self, x, y):
        self.center_x = x
        self.center_y = y
        self.corners = None

    def calculate_corners(self):
        if self.corners is not None:
            return self.corners
        """Get OBB corner points in world coordinates"""
        half_length = (self.length) / 2 - .5
        half_width = (self.width) / 2 - .5
        direction, normal = self.derive_direction_and_normal()

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
        self.corners = [(int(round(x)), int(round(y))) for x, y in corners]

        return self.corners

    def iterate_covered_pixels(self):
        corners = self.calculate_corners()
        xs = [c[0] for c in corners]
        ys = [c[1] for c in corners]

        min_x, max_x = int(math.floor(min(xs))), int(math.ceil(max(xs)))
        min_y, max_y = int(math.floor(min(ys))), int(math.ceil(max(ys)))

        pixels = []
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                if self.is_point_inside(x + 0.5, y + 0.5):  # Pixel center check
                    pixels.append((x, y))
        return pixels
    def merge_aligned(self, other):
        """
        Merge this CollisionBox with another *parallel* CollisionBox to form
        a larger bounding box that encloses them both.

        Returns:
            CollisionBox: A new box encompassing both.
        Raises:
            ValueError: If boxes are not parallel (cannot be merged this way).
        """

        # 1) Check parallel (same rotation or differs by 180)
        if not self.is_parallel_to(other):
            raise ValueError("Boxes are not aligned (not parallel) and cannot be merged.")

        # 2) Get this box's direction and normal (they're valid for both if parallel)
        direction, normal = self.derive_direction_and_normal()

        # 3) Gather corners from both boxes
        corners_self = self.calculate_corners()
        corners_other = other.calculate_corners()
        all_corners = corners_self + corners_other

        def dot(px, py, qx, qy):
            """Dot product of 2D vectors (px, py) · (qx, qy)."""
            return px * qx + py * qy

        # 4) Project corners onto direction and normal to find combined min/max
        dir_values = []
        norm_values = []
        for (cx, cy) in all_corners:
            dir_val = dot(cx, cy, direction[0], direction[1])
            norm_val = dot(cx, cy, normal[0], normal[1])
            dir_values.append(dir_val)
            norm_values.append(norm_val)

        min_dir, max_dir = min(dir_values), max(dir_values)
        min_norm, max_norm = min(norm_values), max(norm_values)

        # 5) The new box length/width spans from min->max along direction/normal
        new_length = max_dir - min_dir
        new_width  = max_norm - min_norm

        # 6) Compute the center by taking midpoint in direction & normal space
        center_dir = 0.5 * (min_dir + max_dir)
        center_norm = 0.5 * (min_norm + max_norm)

        # 7) Convert that (center_dir, center_norm) back to world coordinates
        #    using direction and normal as a 2D basis
        center_x = center_dir * direction[0] + center_norm * normal[0]
        center_y = center_dir * direction[1] + center_norm * normal[1]

        # 8) Create a new bounding box
        merged_box = CollisionBox(
            center_x=center_x,
            center_y=center_y,
            width=new_width,
            length=new_length,
            rotation=self.rotation   # same as 'other' since they are parallel
        )
        return merged_box