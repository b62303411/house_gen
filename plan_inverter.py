import json
import os

# Replace with your actual plan dimensions
PLAN_WIDTH = 1000
PLAN_HEIGHT = 1000

INPUT_PATH = "resources/experiment_floorplan.json"
OUTPUT_PATH = "resources/corrected_floorplan.json"


def convert_point(x, y):
    # Flip both X and Y → 180 rotation
    # Flip X again → final left-right mirror
    return PLAN_WIDTH - x, PLAN_HEIGHT - y


def fix_coordinates(data):
    pixel_to_meter = 0.028
    for node in data.get("nodes", []):
        x = node["x"]
        y = node["y"]
        new_x = x * pixel_to_meter
        new_y = y * pixel_to_meter
        node["x"] = new_x
        node["y"] = new_y

    for edge in data.get("edges", []):
        for opening in edge.get("openings", []):
            width = opening.get("width")
            new_width = width * pixel_to_meter
            opening["width"] = new_width
            center_x = opening.get("center_x")
            opening["center_x"] = center_x * pixel_to_meter

    return data


def main():
    with open(INPUT_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    fixed_data = fix_coordinates(data)

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(fixed_data, f, indent=4)

    print(f"✅ Saved corrected file to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
