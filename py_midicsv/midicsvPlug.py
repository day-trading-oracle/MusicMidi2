import os
import sys
import re
import glob
from py_midicsv_program.py_midicsv.midi.fileio import FileWriter

# Add the py_midicsv directory to the Python path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PYMIDICSV_DIR = os.path.join(SCRIPT_DIR, 'py_midicsv')
sys.path.append(PYMIDICSV_DIR)

# Import the specific converters
from py_midicsv_program.py_midicsv.csvmidi import parse as csv_to_midi
from py_midicsv_program.py_midicsv.midicsv import parse as midi_to_csv

def get_base_filename(filename):
    """Extract the base name without version numbers and extension."""
    # Remove extension
    base = os.path.splitext(filename)[0]
    # Remove version numbers (e.g., '_v1', '_copy', '_copy 2')
    base = re.sub(r'[\s_]+(v\d+|copy(\s+\d+)?|validation)$', '', base)
    return base

def get_next_version(directory, base_name, extension):
    """Get the next available version number for a file."""
    pattern = f"{base_name}*{extension}"
    existing_files = glob.glob(os.path.join(directory, pattern))
    if not existing_files:
        return 1
    
    version_numbers = []
    for file in existing_files:
        match = re.search(r'_v(\d+)' + extension.replace('.', '\.') + '$', file)
        if match:
            version_numbers.append(int(match.group(1)))
    
    return max(version_numbers + [0]) + 1

def convert_and_validate(input_file, output_dir):
    """
    Convert a file from CSV to MIDI and back to CSV, then validate the result.
    Uses specific csvmidi.py and midicsv.py converters.
    """
    try:
        # Get base name without version numbers
        input_base = get_base_filename(os.path.basename(input_file))
        
        # Generate output file paths with versioning
        midi_version = get_next_version(output_dir, input_base, '.mid')
        midi_file = os.path.join(output_dir, f"{input_base}_v{midi_version}.mid")
        validation_csv = os.path.join(output_dir, f"{input_base}_validation.csv")
        
        print(f"\nProcessing {input_base}:")
        print(f"1. CSV → MIDI (version {midi_version})...")
        
        # First conversion: CSV to MIDI using csvmidi.py
        with open(input_file, 'r') as csv_file:
            try:
                midi_data = csv_to_midi(csv_file)
                with open(midi_file, 'wb') as midi_file_out:
                    writer = FileWriter(midi_file_out)
                    writer.write(midi_data)
                print(f"   ✓ MIDI file created: {os.path.basename(midi_file)}")
            except Exception as e:
                print(f"   ❌ CSV to MIDI conversion failed: {str(e)}")
                return False
            
        print("2. MIDI → CSV (validation)...")
        
        # Second conversion: MIDI back to CSV using midicsv.py
        with open(midi_file, 'rb') as midi_file_in:
            try:
                csv_data = midi_to_csv(midi_file_in)
                with open(validation_csv, 'w') as csv_file_out:
                    csv_file_out.writelines(csv_data)
                print(f"   ✓ Validation CSV created: {os.path.basename(validation_csv)}")
            except Exception as e:
                print(f"   ❌ MIDI to CSV conversion failed: {str(e)}")
                return False
            
        print("3. Comparing files...")
        return compare_csv_files(input_file, validation_csv, midi_file)
        
    except Exception as e:
        print(f"❌ Error during conversion cycle: {str(e)}")
        return False

def compare_csv_files(original_csv, validation_csv, midi_file):
    """Compare original CSV with validation CSV, ignoring timing differences."""
    try:
        def read_file_with_comments(filepath):
            lines = []
            with open(filepath, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        if line.startswith('#'):
                            # Preserve comments exactly as they are
                            lines.append(line)
                        else:
                            # Clean up other lines
                            parts = [p.strip() for p in line.split(',')]
                            lines.append(', '.join(parts))
            return lines

        original_lines = read_file_with_comments(original_csv)
        validation_lines = read_file_with_comments(validation_csv)

        # First, handle the header line specially to check track count
        orig_header = next((l for l in original_lines if "Header" in l), None)
        val_header = next((l for l in validation_lines if "Header" in l), None)
        
        if orig_header and val_header:
            orig_parts = orig_header.split(',')
            val_parts = val_header.split(',')
            if orig_parts[4].strip() != val_parts[4].strip():
                print("❌ Track count mismatch in header!")
                print(f"Original: {orig_header}")
                print(f"Converted: {val_header}")
                return False

        # Compare lengths excluding comments
        orig_events = [l for l in original_lines if not l.startswith('#')]
        val_events = [l for l in validation_lines if not l.startswith('#')]
        
        if len(orig_events) != len(val_events):
            print("❌ Files have different number of events:")
            print(f"Original: {len(orig_events)} events")
            print(f"Converted: {len(val_events)} events")
            return False

        # Compare each line ignoring timing differences
        differences = []
        meaningful_differences = []
        for i, (orig, conv) in enumerate(zip(orig_events, val_events), 1):
            if orig != conv:
                differences.append((i, orig, conv))
                
                # Parse the lines to compare non-timing elements
                orig_parts = [p.strip() for p in orig.split(',')]
                conv_parts = [p.strip() for p in conv.split(',')]
                
                # Check if difference is only in timing
                if len(orig_parts) == len(conv_parts) and len(orig_parts) > 2:
                    # Compare all parts except timing (second element)
                    orig_non_timing = [orig_parts[0]] + orig_parts[2:]
                    conv_non_timing = [conv_parts[0]] + conv_parts[2:]
                    
                    if orig_non_timing != conv_non_timing:
                        meaningful_differences.append((i, orig, conv))

        if differences:
            print(f"\n❌ {len(differences)} differences found, {len(meaningful_differences)} are non-timing differences.")
            
            if meaningful_differences:
                print("\nMeaningful differences (not just timing):")
                for line_num, orig, conv in meaningful_differences[:5]:  # Show first 5 meaningful differences
                    print(f"\nLine {line_num}:")
                    print(f"Original : {orig}")
                    print(f"Converted: {conv}")
                
                if len(meaningful_differences) > 5:
                    print(f"\n... and {len(meaningful_differences) - 5} more meaningful differences.")
                
                return False
            else:
                print("\nAll differences are related to timing values only, which is expected.")
                print("✓ Conversion validated successfully despite timing differences!")
                print(f"\nFiles created:")
                print(f"- MIDI: {os.path.basename(midi_file)}")
                print(f"- Validation CSV: {os.path.basename(validation_csv)}")
                return True
        else:
            print("✓ Conversion validated successfully!")
            print(f"\nFiles created:")
            print(f"- MIDI: {os.path.basename(midi_file)}")
            print(f"- Validation CSV: {os.path.basename(validation_csv)}")
            return True

    except Exception as e:
        print(f"❌ Error comparing files: {str(e)}")
        return False

def list_files(directory, extension):
    """List files in a directory with a specific extension."""
    return [f for f in os.listdir(directory) if f.endswith(extension)]

def convert_midi_to_csv(input_file, output_dir):
    """Convert a MIDI file to CSV format."""
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    output_file = os.path.join(output_dir, f"{base_name}.csv")
    with open(input_file, 'rb') as midi_file:
        csv_output = midi_to_csv(midi_file)
        with open(output_file, 'w') as csv_file:
            csv_file.writelines(csv_output)
    print(f"Successfully converted to {output_file}")

def main():
    print("MIDI-CSV Converter with Validation")
    print("=================================")
    
    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = r"C:\ProgramData\DockerDesktop\DockerDesktopWSL\Coding\MusicMidi2\py_midicsv_program\Input"
    output_dir = r"C:\ProgramData\DockerDesktop\DockerDesktopWSL\Coding\MusicMidi2\py_midicsv_program\Output"
    
    # Ensure directories exist
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    
    # List available files
    midi_files = list_files(input_dir, '.mid')
    csv_files = list_files(input_dir, '.csv')
    
    if not midi_files and not csv_files:
        print("No MIDI or CSV files found in the Input directory.")
        return
    
    print("Available files:")
    for i, file in enumerate(midi_files + csv_files, 1):
        print(f"{i}. {file}")
    
    # Prompt user to select a file
    choice = int(input("Select a file number: ")) - 1
    selected_file = (midi_files + csv_files)[choice]
    selected_file_path = os.path.join(input_dir, selected_file)
    
    # Determine file type and prompt for conversion
    if selected_file.endswith('.mid'):
        action = input("Convert MIDI to CSV? (y/n): ").strip().lower()
        if action == 'y':
            convert_midi_to_csv(selected_file_path, output_dir)
    elif selected_file.endswith('.csv'):
        action = input("Convert CSV to MIDI? (y/n): ").strip().lower()
        if action == 'y':
            convert_and_validate(selected_file_path, output_dir)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {str(e)}")
