from copy import copy

from shapely import Polygon, Point, LineString
from shapely.affinity import translate

from floor_plan_reader.math.vector import Vector


class RayTrace:

    @staticmethod
    def move_until_invalid(blob, tip_rect, direction, width=4.0, step=1.0, max_steps=100):
        steps = 0
        moved = copy(tip_rect)
        for _ in range(max_steps):
            moved = translate(moved, direction.dx(), direction.dy())
            if blob.intersects(moved):
                steps += 1
            else:
                break

        return moved, steps

    @staticmethod
    def trace_ray_along_direction(blob_polygon, center, direction, width=4.0, step=1.0, max_steps=100):
        max_distance = 300
        """Measure extent along a given direction vector (dx, dy) properly.
       - First, crawl backward to find the start.
       - Then, count forward to find the total steps.
        """
        d = Vector(direction)
        x = center.x
        y = center.y

        d_reverse = d.copy()
        d_r = d_reverse.opposite()

        end = Point(x + d.dx() * max_distance, y + d.dy() * max_distance)
        origin = Point(x + d_r.dx() * max_distance, y + d_r.dy() * max_distance)

        ray = LineString([origin, end])
        intersection = ray.intersection(blob_polygon.exterior)
        points = []
        # intersection.coords
        steps = 0
        if intersection.geom_type == 'Point':
            return intersection

        elif intersection.geom_type in ['MultiPoint', 'LineString', 'MultiLineString']:
            # For MultiPoint: return closest one
            if intersection.geom_type == 'MultiPoint':
                points = list(intersection.geoms)

            elif intersection.geom_type == 'LineString':
                points = [Point(c) for c in intersection.coords]

            elif intersection.geom_type == 'MultiLineString':
                for line in intersection.geoms:
                    points.extend([Point(c) for c in line.coords])
        elif intersection.geom_type == "GeometryCollection":
                for geom in intersection.geoms:
                    if geom.geom_type == "Point":
                        points.append(geom)
                    elif geom.geom_type in ["LineString", "LinearRing"]:
                        points.extend([Point(c) for c in geom.coords])
                    elif geom.geom_type == "MultiLineString":
                        for line in geom.geoms:
                            points.extend([Point(c) for c in line.coords])
                    elif geom.geom_type == "MultiPoint":
                        points.extend(geom.geoms)

        # Sort by distance from origin (closest first)
        points.sort(key=lambda p: origin.distance(p))
        #return points[0], points[1]  # Backward, forward

        min_x = min(pt.x for pt in points)
        max_x = max(pt.x for pt in points)
        min_y = min(pt.y for pt in points)
        max_y = max(pt.y for pt in points)
        steps = points[0].distance(points[1])
        return steps, [points[0], points[1]]
