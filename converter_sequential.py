import csv
import json
import argparse
import re

def csv_to_json(csv_path, json_path):
    """
    Converts a dialogue CSV file to JSON.
    Handles multiple examples from sequential columns (e.g., examples, examples-2, examples-3, ...).
    """
    dialogue_data = {}
    try:
        with open(csv_path, mode='r', encoding='utf-8-sig') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                node_id = row.get("ID")
                if not node_id:
                    continue

                # --- MODIFIED SECTION START ---
                # Find and sort all 'examples-X' columns to ensure correct order
                example_cols = {}
                for key, value in row.items():
                    if key == 'examples' and value and value.strip():
                        example_cols[1] = value
                    else:
                        match = re.match(r'examples-(\d+)', key)
                        if match and value and value.strip():
                            num = int(match.group(1))
                            example_cols[num] = value
                
                # Create the final sorted list of examples
                examples = [example_cols[i] for i in sorted(example_cols.keys())]
                # --- MODIFIED SECTION END ---

                choices = []
                if row.get("choices_nextNode") and row["choices_nextNode"].strip():
                    choices.append({
                        "text": row.get("choices_text", ""),
                        "nextNode": row.get("choices_nextNode", "")
                    })

                dialogue_data[node_id] = {
                    "character": row.get("character", ""),
                    "goal": row.get("goal", ""),
                    "examples": examples,
                    "choices": choices
                }

        with open(json_path, mode='w', encoding='utf-8') as json_file:
            json.dump(dialogue_data, json_file, ensure_ascii=False, indent=4)

        print(f"✅ Successfully converted '{csv_path}' to '{json_path}'")

    except FileNotFoundError:
        print(f"❌ Error: The file '{csv_path}' was not found.")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")


def json_to_csv(json_path, csv_path):
    """
    Converts a dialogue JSON file to a CSV format.
    Splits the 'examples' list into sequential columns (examples, examples-2, ...).
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)

        # --- MODIFIED SECTION START ---
        # First, find the maximum number of examples in any node to define the header
        max_examples = 0
        for node_id, content in data.items():
            num_examples = len(content.get('examples', []))
            if num_examples > max_examples:
                max_examples = num_examples

        base_fieldnames = ['ID', 'goal', 'others', 'character', 'choices_text', 'choices_nextNode']
        example_fieldnames = ['examples']
        if max_examples > 1:
            example_fieldnames.extend([f'examples-{i}' for i in range(2, max_examples + 1)])
        
        # Combine base headers with example headers
        # A more logical column order:
        final_fieldnames = ['ID', 'goal', 'others'] + example_fieldnames + ['character', 'choices_text', 'choices_nextNode']
        # --- MODIFIED SECTION END ---

        with open(csv_path, 'w', newline='', encoding='utf-8-sig') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=final_fieldnames)
            writer.writeheader()

            for node_id, content in data.items():
                row_data = {
                    'ID': node_id,
                    'goal': content.get('goal', ''),
                    'others': '',
                    'character': content.get('character', ''),
                }

                # --- MODIFIED SECTION START ---
                # Split the examples list into separate columns
                examples_list = content.get('examples', [])
                for i, example_text in enumerate(examples_list):
                    if i == 0:
                        row_data['examples'] = example_text
                    else:
                        row_data[f'examples-{i + 1}'] = example_text
                # --- MODIFIED SECTION END ---
                
                choice = content.get('choices', [{}])[0] if content.get('choices') else {}
                row_data['choices_text'] = choice.get('text', '')
                row_data['choices_nextNode'] = choice.get('nextNode', '')
                
                writer.writerow(row_data)

        print(f"✅ Successfully converted '{json_path}' to '{csv_path}'")

    except FileNotFoundError:
        print(f"❌ Error: The file '{json_path}' was not found.")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")


if __name__ == "__main__":
    # Same argument parser as before
    parser = argparse.ArgumentParser(description="A script to convert between dialogue JSON and CSV formats.", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('direction', choices=['csv2json', 'json2csv'], help="The conversion direction.")
    parser.add_argument('input_file', help="Path to the source file for conversion.")
    parser.add_argument('output_file', help="Path to the destination file.")
    args = parser.parse_args()
    if args.direction == 'csv2json':
        csv_to_json(args.input_file, args.output_file)
    elif args.direction == 'json2csv':
        json_to_csv(args.input_file, args.output_file)