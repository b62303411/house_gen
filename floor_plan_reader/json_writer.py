import json
import logging
import threading


class JsonWriter:
    def __init__(self):
        pass

    def save_floorplan_json(self, filename, floorplan_dict):
        """
        Write the final floorplan dict to a JSON file.
        """
        with open(filename, "w") as f:
            json.dump(floorplan_dict, f, indent=2)
        logging.info(f"JSON saved to {filename}")

    def save_floorplan_async(self, filename, data):
        """
        Spawns a new thread to save the floorplan without blocking the main thread.
        """
        thread = threading.Thread(target=self.save_floorplan_json,
                                  args=(filename, data),
                                  daemon=True)
        thread.start()

    def build_floorplan_json(self, result_info, walls, furnitures=None):
        """
        1) Subdivide walls at intersections -> segments
        2) Convert segments -> (nodes, edges)
        3) Return final JSON-like dict
        """
        # segments = subdivide_walls(walls)
        # nodes, edges = segments_to_mesh(segments)
        nodes = []
        edges = []
        i = 1
        for n in result_info['nodes']:
            # n.id=f"N{i}"
            nodes.append(n.get_json())
            i += 1
        i = 1
        for e in result_info['edges']:
            json_str = e.get_json()
            edges.append(json_str)

        result = {
            "nodes": nodes,
            "edges": edges,
            "furnitures": []
        }
        self.save_floorplan_async("experiment_floorplan.json", result)
        return result
