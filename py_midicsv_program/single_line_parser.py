import os
import sys

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from py_midicsv.csvmidi import parse as csv_to_midi
from py_midicsv.midi.fileio import FileWriter

def preprocess_single_line_csv(input_path, output_path):
    """Converts a single-line CSV into multi-line format for the parser."""
    with open(input_path, 'r') as f:
        content = f.read()
    
    # Split by commas, but preserve commas inside quotes
    events = []
    in_quotes = False
    current_event = []
    current_token = ""
    
    for char in content:
        if char == '"':
            in_quotes = not in_quotes
            current_token += char
        elif char == ',' and not in_quotes:
            current_event.append(current_token.strip())
            current_token = ""
            if len(current_event) >= 3:  # Check if we have at least track, time, event_type
                events.append(current_event)
                current_event = []
        else:
            current_token += char
    
    # Add the last token and event
    if current_token:
        current_event.append(current_token.strip())
    if current_event:
        events.append(current_event)
    
    # Write the reformatted file
    with open(output_path, 'w') as f:
        for event in events:
            f.write(", ".join(event) + "\n")

    print(f"Converted {input_path} to {output_path}")
    return output_path

def convert_file(input_file):
    """Convert a single-line CSV file to proper multi-line format."""
    # Get base name without extension
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    
    # Create output path in Input folder with _converted suffix
    input_dir = os.path.dirname(input_file)
    output_file = os.path.join(input_dir, f"{base_name}_converted.csv")
    
    # Process the file
    return preprocess_single_line_csv(input_file, output_file)

def list_input_files(input_dir):
    """List CSV files in the Input directory."""
    csv_files = [f for f in os.listdir(input_dir) if f.endswith('.csv')]
    return csv_files

if __name__ == "__main__":
    # Set input directory
    input_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Input")
    
    # Ensure input directory exists
    if not os.path.exists(input_dir):
        print(f"Error: Input directory {input_dir} not found.")
        sys.exit(1)
    
    # Get list of CSV files
    csv_files = list_input_files(input_dir)
    
    if not csv_files:
        print("No CSV files found in the Input directory.")
        sys.exit(1)
    
    # Display files for selection
    print("Available CSV files:")
    for i, file in enumerate(csv_files, 1):
        print(f"{i}. {file}")
    
    # Get user selection
    while True:
        try:
            choice = int(input("\nSelect a file number to convert: "))
            if 1 <= choice <= len(csv_files):
                break
            else:
                print(f"Please enter a number between 1 and {len(csv_files)}")
        except ValueError:
            print("Please enter a valid number")
    
    # Convert the selected file
    selected_file = csv_files[choice - 1]
    input_file_path = os.path.join(input_dir, selected_file)
    
    print(f"\nConverting {selected_file}...")
    convert_file(input_file_path)