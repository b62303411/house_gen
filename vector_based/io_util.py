import json
import os

from typing import List, Tuple

from shapely import Polygon, Point
from shapely.geometry import mapping, shape

from floor_plan_reader.math.vector import Vector


class IoUtil:
    @staticmethod
    def save_blob_with_seeds(filepath: str, blob_polygon: Polygon, seed_polygons: List[Polygon], blob_id: str = None):
        data = {
            "id": blob_id or os.path.splitext(os.path.basename(filepath))[0],
            "blob_polygon": mapping(blob_polygon),
            "seed_rectangles": [ { "polygon":mapping(polygon),"center":mapping(center),"direction":direction.direction} for (center, polygon,direction) in seed_polygons]
        }
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
    @staticmethod
    def load_blob_with_seed_centers(filepath: str) -> Tuple[str, Polygon, List[Tuple[Point, Polygon, Vector]]]:
        with open(filepath, "r") as f:
            data = json.load(f)

        blob_polygon = shape(data["blob_polygon"])
        seed_polygons = [
            (
                shape(seed["center"]),
                shape(seed["polygon"]),
                Vector(seed["direction"])  # or your Direction class if you have one
            )
            for seed in data["seed_rectangles"]
        ]
        blob_id = data.get("id", os.path.splitext(os.path.basename(filepath))[0])
        return blob_id, blob_polygon, seed_polygons