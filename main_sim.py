# ------------------------------------------------------------------------------
# Example usage
# ------------------------------------------------------------------------------
import os
import sys
import faulthandler
faulthandler.enable()
from floor_plan_reader.simulation import Simulation

# This ensures Python can locate "my_package" as a subdirectory
script_dir = os.path.dirname(__file__)   # Directory of main.py
package_path = os.path.join(script_dir, 'floor_plan_reader')
if package_path not in sys.path:
    sys.path.append(package_path)

if __name__ == "__main__":
    # Provide a path to your image
    s = Simulation()
    s.run_ant_simulation(
        image_path="floor_plans/fp2.png",
        image_path_filtered="dark_tones_only.png",
        threshold=200,
        num_ants=200,
        allow_revisit=True
    )