import json
import logging
import threading


class JsonWriter:
    def __init__(self):
        pass

    def save_floorplan_json(self,filename, floorplan_dict):
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
    def build_floorplan_json(self,result_info,walls, furnitures=None):
        """
        1) Subdivide walls at intersections -> segments
        2) Convert segments -> (nodes, edges)
        3) Return final JSON-like dict
        """
        #segments = subdivide_walls(walls)
        #nodes, edges = segments_to_mesh(segments)
        nodes = []
        edges = []
        i =1
        for n in result_info['intersections']:
            n.id=f"N{i}"
            nodes.append(n.get_json())
            i+=1
        i =1
        for l in result_info['lines']:

            if len(l.seg.nodes) > 1:
                seg = l.seg
                my_list = list(seg.nodes)
                e = {"id": f"Ext_{i}",
                     "start_node":my_list[0].id, "end_node": my_list[1].id,
                     "wall_type": "exterior",
                     "stud_type":"2x6",
                     "height": 2.7432}
                edges.append(e)
            i +=1
        result = {
            "nodes": nodes,
            "edges": edges,
            "furnitures":[]
        }
        self.save_floorplan_async("experiment_floorplan.json",result)
        return result