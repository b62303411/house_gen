import os

import bpy

from furnitures_gen.furniture_factory import FurnitureFactory


class AssetGen:
  def __init__(self):
      pass


if __name__ == "__main__":
    FurnitureFactory.create_furniture_prototypes()

    # Save result to .blend
    output_path = os.path.abspath("generated_assets.blend")
    bpy.ops.wm.save_as_mainfile(filepath=output_path)