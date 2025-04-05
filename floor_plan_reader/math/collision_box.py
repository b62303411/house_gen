import logging
import math
from decimal import Decimal

from shapely import Polygon, LineString, Point

from floor_plan_reader.math.Constants import Constants
from floor_plan_reader.math.math_segments import combine_segments_decimal
from floor_plan_reader.math.points_logic import Points_Logic
from floor_plan_reader.math.vector import Vector


class CollisionBox:
    def __init__(self, center_x, center_y, width, length, rotation):
        self.center_x = center_x
        self.center_y = center_y
        self.width = float(width)
        self.length = float(length)
        self.rotation = int(rotation)
        self.default_direction = (1, 0)
        self.corners = None
        self._direction = None
        self.center_line = None
        self.points_forward = None
        self.points_backward = None
        self.polygon = None
        self._cached_pixels  = None

    def __eq__(self, other):
        if not isinstance(other, CollisionBox):
            return False
        return (self.center_x, self.center_y, self.width, self.length, self.rotation) == \
            (other.center_x, other.center_y, other.width, other.length, other.rotation)

    def __hash__(self):
        return hash((self.center_x, self.center_y, self.width, self.length, self.rotation))

    def set_width(self, width):
        self.width = float(width)
        self.reset_cache()

    def set_length(self, length):
        self.length = float(length)
        self.reset_cache()

    def copy(self):
        """
        Return a new CollisionBox that is a copy of this one.
        """
        new_box = CollisionBox(
            center_x=self.center_x,
            center_y=self.center_y,
            width=self.width,
            length=self.length,
            rotation=self.rotation
        )
        return new_box

    def get_area(self):
        return self.width * self.length

    def get_direction(self):
        if self._direction is None:
            angle_deg = round(self.rotation / 45.0) * 45 % 360
            direction = Constants.DIRECTIONS_8.get(angle_deg)
            self._direction = direction.normalize()
        return self._direction.copy()

    def get_vector(self):
        dir = self.get_direction()
        vector = dir * self.length
        return vector

    def get_center(self):
        return self.center_x, self.center_y

    def get_center_as_vector(self):
        return Vector((self.center_x, self.center_y))

    def area_of_triangle(self, A, B, C):
        return abs((A[0] * (B[1] - C[1]) + B[0] * (C[1] - A[1]) + C[0] * (A[1] - B[1])) / 2.0)

    def get_polygon(self):
        if self.polygon is None:
            corners = self.calculate_corners()
            self.polygon = Polygon(corners)  # Create the polygon
        return self.polygon

    def is_point_inside(self, x, y):
        poly = self.get_polygon()
        minx, miny, maxx, maxy = poly.bounds
        if x < minx or x > maxx or y < miny or y > maxy:
            return False
        point = Point(x,y)
        poly = self.get_polygon()
        return poly.contains(point)

    def line_equation(self, p1, p2, tol=1e-9):
        """
        Convert two points (x1,y1), (x2,y2) into a normalized (A,B,C) for the line A*x + B*y + C=0.

        Returns:
            (A, B, C) as floats in a unique normalized form.
            If p1 and p2 are the same point, returns None (undefined line).
        """
        (x1, y1), (x2, y2) = p1, p2

        dx = x2 - x1
        dy = y2 - y1

        # If the two points are effectively the same, can't form a valid line
        if abs(dx) < tol and abs(dy) < tol:
            return None

        A = dy
        B = -dx
        C = dx * y1 - dy * x1  # from formula: x2*y1 - x1*y2 rearranged

        # Normalize so that (A,B) has length = 1
        norm = math.hypot(A, B)
        if norm < tol:
            return None

        A /= norm
        B /= norm
        C /= norm

        # Enforce a sign convention so (A,B,C) is unique.
        # e.g., if A < 0 or A=0 and B<0 => multiply all by -1
        # This ensures each line is identified by a unique triplet sign.
        if A < -tol or (abs(A) < tol and B < -tol):
            A, B, C = -A, -B, -C

        return (A, B, C)

    def are_same_line(self, p1, p2, p3, p4, tol=1e-9):
        """
        Check whether the infinite lines defined by segments p1->p2 and p3->p4 are the same.

        Args:
            p1, p2, p3, p4: (x,y) points for two line segments.
            tol: numerical tolerance

        Returns:
            bool: True if they define the same infinite line, False otherwise.
        """
        line1 = self.line_equation(p1, p2, tol)
        line2 = self.line_equation(p3, p4, tol)

        # If either is None, it means degenerate segment => can't define a valid line
        if line1 is None or line2 is None:
            return False

        A1, B1, C1 = line1
        A2, B2, C2 = line2

        # Compare with tolerance. Two lines are same if each coefficient is near-equal
        if (abs(A1 - A2) < tol and abs(B1 - B2) < tol and abs(C1 - C2) < tol):
            return True
        else:
            return False

    def is_on_same_axis_as(self, other, a_t=1, tolerance=5):
        if not self.is_parallel_to(other):
            return False

        dx1, dy1 = self.get_direction().direction
        dx2, dy2 = other.get_direction().direction
        # 1) Check parallel: cross product of directions ~ 0
        # cross(d1, d2) = dx1*dy2 - dy1*dx2
        cross_dir = dx1 * dy2 - dy1 * dx2
        if abs(cross_dir) > a_t:
            return False  # directions not parallel => different lines
        cx1, cy1 = self.get_center()
        cx2, cy2 = other.get_center()
        # 2) Check collinearity: the vector between centers must also be parallel to d1 (or d2)
        # vector (cx2-cx1, cy2-cy1) should have cross with d1 ~ 0
        dcx = cx2 - cx1
        dcy = cy2 - cy1
        cross_centers = dcx * dy1 - dcy * dx1
        if abs(cross_centers) > 10:
            return False  # center offset is not along the shared direction => parallel lines but offset

        # If both checks pass => same infinite line
        return True

    @classmethod
    def from_dict(cls, data):
        """
        Reconstruct a CollisionBox from a dictionary with the same keys.
        """
        return cls(
            center_x=data["center_x"],
            center_y=data["center_y"],
            width=data["width"],
            length=data["length"],
            rotation=data["rotation"]
        )

    def to_dict(self):
        return {
            "center_x": self.center_x,
            "center_y": self.center_y,
            "width": self.width,
            "length": self.length,
            "rotation": self.rotation
        }

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
        nx, ny = self.get_normal().direction

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


        # Direction vector (rotated from default direction (1,0))
        direction = self.get_direction()

        # Normal vector (rotated 90 degrees from direction)
        normal = direction.get_normal().normalize()

        return direction, normal

    def is_parallel_to(self, other, tolerance=1e-5):
        angle_diff = abs(self.rotation - other.rotation) % 180
        return angle_diff < tolerance or abs(angle_diff - 180) < tolerance

    def is_overlapping(self, other):
        return self.calculate_overlap_ratio(other) > 0.1
        # return other.is_point_inside(self.center_x, self.center_y)


    def get_center_line(cb):
        """
        Returns ((x1, y1), (x2, y2)) for the center line of a CollisionBox
        using length and rotation, ignoring width.
        """
        direction, _ = cb.derive_direction_and_normal()
        dx, dy = direction.direction
        half_len = cb.length / 2.0
        cx, cy = cb.center_x, cb.center_y

        x1 = cx - dx * half_len
        y1 = cy - dy * half_len
        x2 = cx + dx * half_len
        y2 = cy + dy * half_len
        return (x1, y1), (x2, y2)

    def get_ray_trace_points(self):
        direction = self.get_direction()
        half_length = self.length / 2.0
        points = []
        for factor in [0.25, 0.5, 0.75]:
            point_x = self.center_x + direction[0] * half_length * factor
            point_y = self.center_y + direction[1] * half_length * factor
            points.append((point_x, point_y))
        return points

    def move_forward(self, lenght):
        dir_ = self.get_direction()
        dir_.scale(lenght)
        self.move(dir_)

    def move_backward(self, lenght):
        dir_ = self.get_direction().opposite()
        dir_.scale(lenght)
        self.move(dir_)

    def move(self, dir_):
        c = self.get_center_as_vector()
        new_c = c + dir_
        self.set_position(new_c.dx(), new_c.dy())
    @staticmethod
    def create_from_line(line, width):
        x1, y1 = line.coords[0]
        x2, y2 = line.coords[-1]

        # Direction vector
        dx = x2 - x1
        dy = y2 - y1
        length = math.hypot(dx, dy)
        if length == 0:
            raise ValueError("Line must have length > 0")
        # Center point
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        # Angle in radians and degrees
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad)
        cb = CollisionBox(cx, cy,width,length,angle_deg)
        return cb

    def get_normal(self):
        dir_ = self.get_direction()
        return dir_.get_normal()

    def get_extended_ray_trace_points(self, max_x, max_y):
        if self.points_forward is None or self.points_forward is None:
            direction = self.get_direction().direction
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
            if len(points_backward) > 0 :
                self.points_backward=points_backward
                self.points_forward=points_forward
            else:
                pass

        return self.points_forward, self.points_backward

    def set_position(self, x, y):
        self.center_x = x
        self.center_y = y
        self.reset_cache()

    def reset_cache(self):
        self.corners = None
        self.points_forward = None
        self.points_backward = None
        self.polygon = None
        self.center_line = None
        self._cached_pixels  = None

    def calculate_overlap_ratio(self, other):
        overlap = self.calculate_overlap(other)
        if self.get_area() == 0:
            return 0
        return overlap / self.get_area()

    def calculate_overlap(self, other):
        corners_self = self.calculate_corners()
        corners_other = other.calculate_corners()

        # Create Polygon objects for both boxes
        polygon_self = Polygon(corners_self)
        polygon_other = Polygon(corners_other)

        # Check if the polygons intersect
        if not polygon_self.intersects(polygon_other):
            return 0  # No overlap

        # Calculate the intersection area
        intersection = polygon_self.intersection(polygon_other)
        return intersection.area

    def calculate_corners(self):
        if self.corners is not None:
            return self.corners
        """Get OBB corner points in world coordinates"""
        half_length = self.length / 2 - .5
        half_width = self.width / 2 - .5
        direction, normal = self.derive_direction_and_normal()

        back = direction.opposite()
        back.scale(half_length)
        front = direction.copy()
        front.scale(half_length)
        left = normal.copy()
        left.scale(half_width)
        position = Vector((self.center_x, self.center_y))
        to_left = position + left + back
        top_right = position - left + back
        bottom_left = position + front + left
        bottom_right = position + front - left

        # Calculate corners without offsets
        top_left = (
            to_left.direction[0],
            to_left.direction[1]  # Y-down adjustment
        )
        bottom_right = (
            bottom_right.direction[0],
            bottom_right.direction[1]  # Y-down adjustment
        )

        # Other corners for completeness
        top_right = (
            top_right.direction[0],
            top_right.direction[1]  # Y-down adjustment
        )
        bottom_left = (
            bottom_left.direction[0],
            bottom_left.direction[1]  # Y-down adjustment
        )

        # Order: [top-left, bottom-left, top-right, bottom-right]
        corners = [top_left, top_right, bottom_right, bottom_left]

        # Apply pixel alignment (rounding) once at the end
        self.corners = [(int(round(x)), int(round(y))) for x, y in corners]

        return self.corners

    def iterate_covered_pixels(self):

        if self._cached_pixels is not None:
            return self._cached_pixels

        wall_polygon = self.get_polygon()
        corners = self.calculate_corners()

        xs = [c[0] for c in corners]
        ys = [c[1] for c in corners]
        min_x, max_x = int(math.floor(min(xs))), int(math.ceil(max(xs)))
        min_y, max_y = int(math.floor(min(ys))), int(math.ceil(max(ys)))

        self._cached_pixels = []
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                center = Point(x + 0.5, y + 0.5)  # Test pixel center
                if wall_polygon.contains(center):
                    self._cached_pixels.append((x, y))
        return self._cached_pixels


    def get_center_line(self):
        """
        Returns a 2D line segment for the box's center line:
        segment start (x1, y1), segment end (x2, y2).
        """
        direction, _ = self.derive_direction_and_normal()
        dx, dy = direction.direction  # e.g. (cosθ, sinθ)
        half_len = self.length / 2.0

        cx, cy = self.center_x, self.center_y
        x1 = cx - dx * half_len
        y1 = cy - dy * half_len
        x2 = cx + dx * half_len
        y2 = cy + dy * half_len

        return (x1, y1), (x2, y2)

    def to_decimal(self, value):
        x = Decimal(value[0])
        y = Decimal(value[1])
        return x, y

    def get_definition(self):
        return self.get_center(), self.get_direction(), self.length

    def merge_aligned2(self, other):
        new_cx, new_cy, dirx, diry, new_length = combine_segments_decimal(
            self, other)
        merged_box = CollisionBox(
            center_x=float(new_cx),
            center_y=float(new_cy),
            width=float(self.width),
            length=float(new_length),
            rotation=self.rotation  # same as 'other' since they are parallel
        )
        return merged_box

    def merge_aligned(self, other, decimal_precision=3):
        """
        Merge this CollisionBox with another *parallel* CollisionBox to form
        a larger bounding box that encloses them both.

        Returns:
            CollisionBox: A new box encompassing both.
        Raises:
            ValueError: If boxes are not parallel (cannot be merged this way).
        """
        rounder = lambda val: round(val, decimal_precision)
        # 1) Check parallel (same rotation or differs by 180)
        if not self.is_parallel_to(other):
            return False
            # raise ValueError("Boxes are not aligned (not parallel) and cannot be merged.")

        self_line = self.get_center_line_string()
        other_line = other.get_center_line_string()
        p = Points_Logic()
        line = p.create_line_from_two_most_distant_points([self_line,other_line])

        merged_box = self.create_from_line(line,self.width)

        return merged_box

    def calculate_rotation_from_direction(self, dx, dy):
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad)
        # Normalize angle to nearest 45 degrees
        angle_deg = round(angle_deg / 45) * 45
        return angle_deg % 360

    def get_center_line_string(self):
        if self.center_line is None:
            (x1, y1), (x2, y2) = self.get_center_line()
            end1 = Point(x1, y1)
            end2 = Point(x2,y2)
            self.center_line = LineString([end1, end2])
        return self.center_line

    def distance_from_center_line(self, point):
        line = self.get_center_line_string()
        p = Point(point.x, point.y)
        logging.debug(f"{p.x}")
        return p.distance(line)

    def get_distance_from(self, collision_box):
        self_point = self.get_center_point()
        other_point = collision_box.get_center_point()
        return self_point.distance(other_point)

    def get_center_point(self):
        center = self.get_center()
        return Point(center)
