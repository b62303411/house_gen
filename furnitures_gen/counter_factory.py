from board_factory import BoardFactory
import bpy

class CounterFactory:
    @staticmethod
    def create_counter(name_prefix, wall, offset, width, height, depth, material=None):
        """Creates a counter aligned with a wall segment, offset to one side or the other."""
        bpy.ops.object.empty_add(type='PLAIN_AXES')
        counter_parent = bpy.context.object
        counter_parent.name = f"{name_prefix}_Counter"
        counter_parent.parent = wall
        counter_parent.location = (wall.location.x + offset, 0, 0)

        base = BoardFactory.add_board(
            parent=counter_parent,
            board_name=f"{name_prefix}_Base",
            length=width,
            height=height,
            depth=depth,
            location=(0, 0, height / 2),
            material=material
        )

        countertop_material = CounterFactory.create_granite_material()
        countertop = BoardFactory.add_board(
            parent=counter_parent,
            board_name=f"{name_prefix}_Countertop",
            length=width + 0.1,  # Slight overhang
            height=0.04,  # Standard thickness
            depth=depth + 0.1,
            location=(0, 0, height + 0.02),
            material=countertop_material
        )

        return counter_parent

    @staticmethod
    def insert_sink(counter, name_prefix, sink_width, sink_depth, sink_height):
        """Creates and inserts a chrome-textured sink inside a counter."""
        chrome_material = bpy.data.materials.new(name="Chrome")
        chrome_material.metallic = 1.0
        chrome_material.roughness = 0.1

        sink = BoardFactory.add_board(
            parent=counter,
            board_name=f"{name_prefix}_Sink",
            length=sink_width,
            height=sink_height,
            depth=sink_depth,
            location=(0, 0, counter.location.z + sink_height / 2),
            material=chrome_material
        )

        print(f"✅ Sink {name_prefix}_Sink inserted into {counter.name}")
        return sink

    @staticmethod
    def create_granite_material():
        """Generates a procedural granite material."""
        granite_material = bpy.data.materials.new(name="Granite")
        granite_material.use_nodes = True
        nodes = granite_material.node_tree.nodes
        nodes.clear()

        output_node = nodes.new(type='ShaderNodeOutputMaterial')
        principled_node = nodes.new(type='ShaderNodeBsdfPrincipled')
        noise_node = nodes.new(type='ShaderNodeTexNoise')

        principled_node.location = (-200, 0)
        noise_node.location = (-400, 0)

        granite_material.node_tree.links.new(principled_node.outputs['BSDF'], output_node.inputs['Surface'])
        granite_material.node_tree.links.new(noise_node.outputs['Color'], principled_node.inputs['Base Color'])

        noise_node.inputs['Scale'].default_value = 50.0
        noise_node.inputs['Detail'].default_value = 5.0
        noise_node.inputs['Roughness'].default_value = 0.6

        return granite_material