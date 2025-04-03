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
    for node in data.get("nodes", []):
        if "point" in node:
            x, y = node["point"]
            new_x, new_y = convert_point(x, y)
            node["point"] = [new_x, new_y]
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
