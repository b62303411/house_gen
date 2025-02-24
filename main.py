import bpy
import math
import os
import sys


def get_script_dir():
    """Get only the directory of the current script without the file name."""
    script_dir = None

    try:
        # Try getting the directory from Blender text editor
        script_path = bpy.context.space_data.text.filepath
        if script_path:
            script_dir = os.path.dirname(os.path.abspath(script_path))  # Ensure only the folder
    except (AttributeError, TypeError):
        pass

    if not script_dir:
        try:
            # Fall back to __file__ attribute
            script_path = os.path.abspath(__file__)
            script_dir = os.path.dirname(script_path)  # Extract only the directory
        except NameError:
            # If all else fails, use Blender's executable directory
            script_dir = os.path.dirname(bpy.app.binary_path)

    return script_dir

script_dir = get_script_dir()
if script_dir not in sys.path:
    sys.path.append(script_dir)
    sys.path.append("E:\workspace\blender_house\house_gen") 

print("Updated script_dir:", script_dir) 
# Debugging: Print sys.path to check if it's added
#print("Updated sys.path:", sys.path)



print("Python Executable:", sys.executable)
print("Python Version:", sys.version)
print("Current Working Directory:", os.getcwd())
#print("Sys Path:", sys.path)
import os

script_dir = "E:\\workspace\\blender_house\\house_gen"
print("Files in script directory:", os.listdir(script_dir))


import frame_factory
import importlib
import materials
import board_factory
import windows
import segment_factory
import house_factory
import bath_thub_factory
importlib.reload(materials)  # Force refresh
importlib.reload(board_factory)
importlib.reload(windows)
importlib.reload(segment_factory)
importlib.reload(house_factory)
importlib.reload(frame_factory)
importlib.reload(frame_factory)
importlib.reload(bath_thub_factory)
from scene_factory import SceneFactory


if __name__ == "__main__":
    SceneFactory.build_scene()