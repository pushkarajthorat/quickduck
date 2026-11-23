import csv
import json
import os
import sys


def json_to_csv():
    # Ensure the user provided the file path argument
    if len(sys.argv) < 2:
        print("Error: Missing input JSON file path.")
        print("Usage: python script.py <path_to_json_file>")
        sys.exit(1)

    # Get the input path from the first argument (sys.argv[1])
    json_path = sys.argv[1]
    csv_path = json_path + ".csv"

    # Verify that the input file actually exists
    if not os.path.exists(json_path):
        print(f"Error: The file '{json_path}' does not exist.")
        sys.exit(1)

    try:
        # Load the JSON data
        with open(json_path, "r", encoding="utf-8") as json_file:
            data = json.load(json_file)

        # Handle both formats: top-level dictionary with "workout plan" key or a direct list
        if isinstance(data, dict) and "workout plan" in data:
            workout_list = data["workout plan"]
        elif isinstance(data, list):
            workout_list = data
        else:
            print("Error: JSON format not recognized. Expected a list or an object containing 'workout plan'.")
            sys.exit(1)

        if not workout_list:
            print("Warning: The JSON file contains an empty workout list.")
            return

        # Dynamically extract all unique keys from the list items to use as headers
        all_keys = set()
        for item in workout_list:
            if isinstance(item, dict):
                all_keys.update(item.keys())
        
        # Ensure 'exercise' is always the first column if it exists
        fieldnames = sorted(list(all_keys))
        if "exercise" in fieldnames:
            fieldnames.remove("exercise")
            fieldnames.insert(0, "exercise")

        # Write data to the CSV file
        with open(csv_path, mode="w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(workout_list)

        print(f"Success! Converted '{json_path}' to '{csv_path}'")

    except json.JSONDecodeError:
        print(f"Error: '{json_path}' is not a valid JSON file.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    json_to_csv()
