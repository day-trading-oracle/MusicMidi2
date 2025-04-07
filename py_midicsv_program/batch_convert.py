import os
import sys

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from py_midicsv.csvmidi import parse as csv_to_midi
from py_midicsv.midi.fileio import FileWriter


def convert_csv_to_midi(csv_file, output_dir):
    """Convert a CSV file to MIDI."""
    try:
        # Get base name without extension
        base_name = os.path.splitext(os.path.basename(csv_file))[0]
        
        # Create output file path
        midi_file = os.path.join(output_dir, f"{base_name}.mid")
        
        # Convert CSV to MIDI
        with open(csv_file, 'r') as csv_input:
            midi_data = csv_to_midi(csv_input)
            
        # Save MIDI file
        with open(midi_file, 'wb') as midi_output:
            writer = FileWriter(midi_output)
            writer.write(midi_data)
            
        print(f"✓ Converted {os.path.basename(csv_file)} to {os.path.basename(midi_file)}")
        return True
    except Exception as e:
        print(f"❌ Error converting {os.path.basename(csv_file)}: {str(e)}")
        return False


def batch_convert():
    """Convert all CSV files in the Input directory to MIDI."""
    # Set directories
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(script_dir, "Input")
    output_dir = os.path.join(script_dir, "Output")
    
    # Ensure directories exist
    if not os.path.exists(input_dir):
        print(f"Error: Input directory {input_dir} not found.")
        return
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Get all CSV files
    csv_files = [f for f in os.listdir(input_dir) if f.endswith('.csv')]
    
    if not csv_files:
        print("No CSV files found in the Input directory.")
        return
    
    print(f"Found {len(csv_files)} CSV files to convert:")
    for i, file in enumerate(csv_files, 1):
        print(f"{i}. {file}")
    
    print("\nStarting batch conversion...")
    
    # Track successful and failed conversions
    successful = 0
    failed = 0
    
    # Convert each file
    for csv_file in csv_files:
        csv_path = os.path.join(input_dir, csv_file)
        result = convert_csv_to_midi(csv_path, output_dir)
        if result:
            successful += 1
        else:
            failed += 1
    
    # Print summary
    print("\nBatch conversion complete!")
    print(f"Successful conversions: {successful}")
    print(f"Failed conversions: {failed}")
    print(f"Output files saved to: {output_dir}")


if __name__ == "__main__":
    print("CSV to MIDI Batch Converter")
    print("===========================\n")
    batch_convert()