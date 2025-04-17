from shapely import GeometryCollection, Point

from floor_plan_reader.id_util import IdUtil
from vector_based.agents.blob import Blob
from vector_based.agents.segment import Segment


class World:
    def __init__(self):
        self.blobs = []
        self.segments = []
        self.agents = []
        self.polygons = []
        self.grid = None
        self.collection = None

    def set_polygons(self, polygons):
        self.collection = GeometryCollection(polygons)
        self.polygons = polygons

    def create_blob(self, poly):
        blob_ = Blob(IdUtil.get_id(), self)
        blob_.poly = poly
        blob_.id = IdUtil.get_id()
        self.agents.append(blob_)

    def create_segment(self, blob, x, y):
        s = Segment(self, blob, x, y, IdUtil.get_id())
        self.segments.append(s)
        self.active_wall = s
        self.segments.append(s)
        self.agents.append(s)

    def is_within_bounds(self, x, y):
        return True

    def get_occupied_id(self, x, y):
        return 0

    def occupy(self, x, y, obj):
        pass

    def is_occupied(self, x, y):
        return False

    def free(self, x, y):
        pass

    def is_food(self, x, y):
        return self.collection.intersects(Point(x, y))

    def run(self):
        agents = self.agents.copy()
        for a in agents:
            a.run()

    def get_shape(self):
        return self.grid.shape()
