import csv
import json
import argparse

def csv_to_json(csv_path, json_path):
    """
    Converts a dialogue CSV file to the specified JSON format.

    Args:
        csv_path (str): The path to the input CSV file.
        json_path (str): The path for the output JSON file.
    """
    dialogue_data = {}
    try:
        with open(csv_path, mode='r', encoding='utf-8-sig') as csv_file:
            # Using -sig encoding to handle potential BOM characters from Excel
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                node_id = row.get("ID")
                if not node_id:
                    continue

                # Collect examples from both 'examples' and 'examples-2' columns
                examples = []
                if row.get("examples") and row["examples"].strip():
                    examples.append(row["examples"])
                if row.get("examples-2") and row["examples-2"].strip():
                    examples.append(row["examples-2"])

                # Construct the 'choices' list
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
    Converts a dialogue JSON file to a CSV format for easy editing.

    Args:
        json_path (str): The path to the input JSON file.
        csv_path (str): The path for the output CSV file.
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)

        with open(csv_path, 'w', newline='', encoding='utf-8-sig') as csv_file:
            # Define the CSV header. The 'others' column is included for manual notes.
            fieldnames = ['ID', 'goal', 'others', 'examples', 'examples-2', 'character', 'choices_text', 'choices_nextNode']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()

            for node_id, content in data.items():
                # Split the 'examples' list into two separate columns
                example1 = content.get('examples', [])[0] if len(content.get('examples', [])) > 0 else ''
                example2 = content.get('examples', [])[1] if len(content.get('examples', [])) > 1 else ''

                # Unpack the 'choices' list (assumes one choice per dialogue node)
                choice = content.get('choices', [{}])[0] if content.get('choices') else {}
                choice_text = choice.get('text', '')
                choice_next_node = choice.get('nextNode', '')

                writer.writerow({
                    'ID': node_id,
                    'goal': content.get('goal', ''),
                    'others': '',  # 'others' field is a placeholder for notes in the CSV
                    'examples': example1,
                    'examples-2': example2,
                    'character': content.get('character', ''),
                    'choices_text': choice_text,
                    'choices_nextNode': choice_next_node
                })

        print(f"✅ Successfully converted '{json_path}' to '{csv_path}'")

    except FileNotFoundError:
        print(f"❌ Error: The file '{json_path}' was not found.")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="A script to convert between dialogue JSON and CSV formats.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument('direction', 
                        choices=['csv2json', 'json2csv'], 
                        help="The conversion direction:\n"
                             "  csv2json: Converts your CSV file to a JSON file.\n"
                             "  json2csv: Converts your JSON file to a CSV file.")
    
    parser.add_argument('input_file', help="Path to the source file for conversion.")
    parser.add_argument('output_file', help="Path to the destination file.")

    args = parser.parse_args()

    if args.direction == 'csv2json':
        csv_to_json(args.input_file, args.output_file)
    elif args.direction == 'json2csv':
        json_to_csv(args.input_file, args.output_file)