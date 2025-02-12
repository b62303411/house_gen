import math
import os
import sys

import frame_factory


def get_script_dir():
    """Get the directory of the current script, handling different contexts."""
    try:
        # First try to get path from text editor
        script_dir = os.path.dirname(bpy.context.space_data.text.filepath)
    except (AttributeError, TypeError):
        try:
            # Fall back to the __file__ attribute
            script_dir = os.path.dirname(os.path.abspath(__file__))
        except NameError:
            # If all else fails, use the Blender executable directory
            script_dir = os.path.dirname(bpy.app.binary_path)

    return script_dir
script_dir = get_script_dir()
if script_dir not in sys.path:
    sys.path.append(script_dir)
import importlib
import materials
import board_factory
import windows
import segment_factory
import house_factory
importlib.reload(materials)  # Force refresh
importlib.reload(board_factory)
importlib.reload(windows)
importlib.reload(segment_factory)
importlib.reload(house_factory)
importlib.reload(frame_factory)
importlib.reload(frame_factory)
from scene_factory import SceneFactory


if __name__ == "__main__":
    SceneFactory.build_scene()