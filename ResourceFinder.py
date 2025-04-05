import json
import os

import os
import json
import bpy  # only needed if you want to load images in Blender


class ResourceFinder:
    def __init__(self, base_dir=None, resource_subfolder="resources"):
        # By default, use the directory containing this .py file as the base
        if base_dir is None:
            base_dir = os.path.dirname(os.path.realpath(__file__))

        self.base_dir = base_dir
        self.resource_dir = os.path.join(self.base_dir, resource_subfolder)

        # Make sure the folder actually exists (optional: raise an error if not)
        if not os.path.isdir(self.resource_dir):
            print(f"Warning: Resource folder does not exist at '{self.resource_dir}'")

    def get(self, resource_name):
        """
           Build the absolute path to a resource file by name, with debug info.
           """
        print(f"[ResourceFinder] Requested resource: '{resource_name}'")
        print(f"[ResourceFinder] Resource directory: '{self.resource_dir}'")

        resource_path = os.path.join(self.resource_dir, resource_name)
        print(f"[ResourceFinder] Full path to look for: '{resource_path}'")
        """
        Build the absolute path to a resource file by name.
        Example: get('w1024.jpg') --> 'E:/.../resources/w1024.jpg'
        """
        resource_path = os.path.join(self.resource_dir, resource_name)
        if not os.path.exists(resource_path):
            raise FileNotFoundError(f"Resource '{resource_name}' not found in {self.resource_dir}")
        return resource_path

    def load_image(self, image_name):
        """
        Load an image into Blender's bpy.data.images by filename.
        """
        path = self.get(image_name)
        return bpy.data.images.load(path)

    def load_json(self, json_name):
        """
        Read a JSON file from your resources folder.
        """
        path = self.get(json_name)
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data


# Create a single instance
_finder_instance = ResourceFinder()


def get_finder():
    """
    Global accessor for the singleton ResourceFinder.
    """
    return _finder_instance
