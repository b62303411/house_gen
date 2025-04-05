from itertools import combinations

from shapely import LineString, Point


class Points_Logic:
    def __init__(self):
        self.collision_box = None
    
    def create_line_from_two_most_distant_points(self,line_strings):
        endpoints = []
        for line in line_strings:
            coords = list(line.coords)
            a = Point(coords[0])
            b = Point(coords[-1])
            endpoints.append(a)
            endpoints.append(b)
        max_dist = -1
        max_pair = (None, None)

        for p1, p2 in combinations(endpoints, 2):
            dist = p1.distance(p2)
            if dist > max_dist:
                max_dist = dist
                max_pair = (p1, p2)

        center_line = LineString([max_pair[0], max_pair[1]])
        return center_line