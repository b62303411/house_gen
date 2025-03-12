class LineToGraph:
    ############################################################
    # STEP 3A: Generate Graph & JSON
    ############################################################
    def generate_graph(walls):
        """
        Create a node/edge graph from line segments.
        We'll label each unique (x, y) as a node. We'll guess 'exterior' if width >= 10, else 'interior'.
        We'll store them in the requested format.
        """
        nodes_dict = {}
        node_list = []

        def register_point(px, py):
            # Round to e.g. 3 decimals
            # Create new ID if we haven't encountered it
            key = (round(px, 3), round(py, 3))
            if key not in nodes_dict:
                nid = f"N{len(nodes_dict)+1}"
                nodes_dict[key] = nid
            return nodes_dict[key]

        edges_list = []
        for i, wall in enumerate(walls, start=1):
            (x1, y1) = wall["start"]
            (x2, y2) = wall["end"]
            id1 = register_point(x1, y1)
            id2 = register_point(x2, y2)

            # guess exterior if width >= 10
            if wall["width"] >= 10:
                wall_type = "exterior"
                stud_type = "2x6"
            else:
                wall_type = "interior"
                stud_type = "2x4"

            edge_id = f"E{i}"
            edges_list.append({
                "id": edge_id,
                "start_node": id1,
                "end_node": id2,
                "wall_type": wall_type,
                "stud_type": stud_type,
                "height": 2.0,
                "openings": []
            })

        # build node_list
        for (x, y), nid in nodes_dict.items():
            node_list.append({
                "id": nid,
                "x": x,
                "y": y
            })

        # sort nodes by numeric part of ID
        def node_sort_key(item):
            return int(item["id"].strip("N"))

        node_list.sort(key=node_sort_key)

        graph = {
            "nodes": node_list,
            "edges": edges_list
        }
        return graph