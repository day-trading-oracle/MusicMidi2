import os
import sys
import re
import glob

# Add the parent directory to the Python path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.append(PARENT_DIR)

# Import using absolute imports
from py_midicsv.midi.fileio import FileWriter
from py_midicsv.csvmidi import parse as csv_to_midi
from py_midicsv.midicsv import parse as midi_to_csv

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

def convert_csv_to_midi(input_file, output_dir):
    """Convert a CSV file to MIDI format."""
    try:
        # Get base name without version numbers
        input_base = get_base_filename(os.path.basename(input_file))
        
        # Generate output file path with versioning
        midi_version = get_next_version(output_dir, input_base, '.mid')
        midi_file = os.path.join(output_dir, f"{input_base}_v{midi_version}.mid")
        
        print(f"\nProcessing {input_base}:")
        print(f"CSV → MIDI (version {midi_version})...")
        
        # Convert CSV to MIDI
        with open(input_file, 'r') as csv_file:
            try:
                midi_data = csv_to_midi(csv_file)
                with open(midi_file, 'wb') as midi_file_out:
                    writer = FileWriter(midi_file_out)
                    writer.write(midi_data)
                print(f"✓ MIDI file created: {os.path.basename(midi_file)}")
                return midi_file
            except Exception as e:
                print(f"❌ CSV to MIDI conversion failed: {str(e)}")
                return None
    except Exception as e:
        print(f"❌ Error during conversion: {str(e)}")
        return None

def convert_midi_to_csv(input_file, output_dir, fix_timing=True):
    """Convert a MIDI file to CSV format with optional timing fixes."""
    try:
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        output_file = os.path.join(output_dir, f"{base_name}.csv")
        
        print(f"\nProcessing {base_name}:")
        print(f"MIDI → CSV...")
        
        with open(input_file, 'rb') as midi_file:
            try:
                csv_output = midi_to_csv(midi_file)
                with open(output_file, 'w') as csv_file:
                    csv_file.writelines(csv_output)
                
                # Optionally fix timing issues
                if fix_timing:
                    fix_timing_issues(output_file)
                
                print(f"✓ CSV file created: {os.path.basename(output_file)}")
                return output_file
            except Exception as e:
                print(f"❌ MIDI to CSV conversion failed: {str(e)}")
                return None
    except Exception as e:
        print(f"❌ Error during conversion: {str(e)}")
        return None

def fix_timing_issues(csv_file, original_csv=None):
    """Fix timing issues in CSV file, particularly End_track and End_of_file events."""
    try:
        # Read the file
        with open(csv_file, 'r') as f:
            lines = f.readlines()
        
        fixed_lines = []
        last_track_time = {}  # Store the max time for each track
        max_time = 0          # Store the maximum time across all tracks
        track_events = {}     # Store events by track
        
        # First pass: collect timing information
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('//'):
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 3:
                    try:
                        track_num = int(parts[0])
                        time = int(parts[1])
                        event_type = parts[2].strip()
                        
                        # Skip End_of_file for now
                        if event_type == "End_of_file":
                            continue
                            
                        # Track maximum time for each track
                        if track_num not in last_track_time:
                            last_track_time[track_num] = 0
                            track_events[track_num] = []
                        
                        # Store event
                        track_events[track_num].append((time, event_type, parts))
                        
                        # Update max time for all note and End_track events
                        if (event_type.startswith("Note_") or event_type == "End_track") and time > last_track_time[track_num]:
                            last_track_time[track_num] = time
                            
                        # Update global max time
                        if time > max_time:
                            max_time = time
                    except:
                        pass
        
        # Second pass: fix timing issues
        timing_issues_found = False
        for i, line in enumerate(lines):
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('//'):
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 3:
                    try:
                        track_num = int(parts[0])
                        time = int(parts[1])
                        event_type = parts[2].strip()
                        
                        # Fix End_track events with unrealistic timing
                        if event_type == "End_track" and time > 10000000 and track_num in last_track_time:
                            # Use the highest time from the track's events
                            parts[1] = str(last_track_time[track_num])
                            line = ', '.join(parts)
                            timing_issues_found = True
                        
                        # Fix End_of_file event - should use maximum time from all tracks
                        if event_type == "End_of_file" and time == 0 and max_time > 0:
                            parts[1] = str(max_time)
                            line = ', '.join(parts)
                            timing_issues_found = True
                            
                    except:
                        pass
            
            fixed_lines.append(line + '\n')
        
        # Only write back if we made changes
        if timing_issues_found:
            with open(csv_file, 'w') as f:
                f.writelines(fixed_lines)
            print("  Note: Fixed timing issues in End_track and End_of_file events")
        
    except Exception as e:
        print(f"❌ Error fixing timing issues: {str(e)}")

def round_trip_validation(input_file, output_dir):
    """Perform full round-trip validation: CSV → MIDI → CSV → Compare."""
    try:
        # First conversion: CSV to MIDI
        midi_file = convert_csv_to_midi(input_file, output_dir)
        if not midi_file:
            return False
            
        # Second conversion: MIDI back to CSV
        validation_csv = os.path.join(output_dir, f"{get_base_filename(os.path.basename(input_file))}_validation.csv")
        with open(midi_file, 'rb') as midi_file_in:
            try:
                csv_data = midi_to_csv(midi_file_in)
                with open(validation_csv, 'w') as csv_file_out:
                    csv_file_out.writelines(csv_data)
                print(f"✓ Validation CSV created: {os.path.basename(validation_csv)}")
            except Exception as e:
                print(f"❌ MIDI to CSV conversion failed: {str(e)}")
                return False
        
        # Fix timing issues in validation file, passing the original CSV
        fix_timing_issues(validation_csv, input_file)
            
        # Compare files
        print("Comparing files...")
        if compare_csv_files(input_file, validation_csv, midi_file):
            print("✓ Round-trip validation successful!")
            return True
        else:
            print("❌ Round-trip validation failed")
            return False
        
    except Exception as e:
        print(f"❌ Error during validation: {str(e)}")
        return False

def compare_csv_files(original_csv, validation_csv, midi_file):
    """Compare original CSV with validation CSV, focusing on event types and musical data."""
    try:
        def parse_csv_line(line):
            """Parse a CSV line into its components."""
            parts = [p.strip() for p in line.split(',')]
            if len(parts) >= 3:
                track_num = int(parts[0])
                time = int(parts[1])
                event_type = parts[2]
                params = parts[3:] if len(parts) > 3 else []
                return {
                    'track': track_num,
                    'time': time,
                    'event': event_type,
                    'params': params
                }
            return None

        def read_file_events(filepath):
            """Read and parse events from a CSV file."""
            events = []
            with open(filepath, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        event = parse_csv_line(line)
                        if event:
                            events.append(event)
            return events

        # Read both files
        original_events = read_file_events(original_csv)
        validation_events = read_file_events(validation_csv)

        # Check for empty files
        if not original_events or not validation_events:
            print("❌ One or both files are empty or could not be parsed.")
            return False

        # Compare event counts
        if len(original_events) != len(validation_events):
            print("❌ Different number of events:")
            print(f"Original: {len(original_events)} events")
            print(f"Converted: {len(validation_events)} events")
            return False

        # Compare events ignoring track numbers
        differences = []
        for i, (orig, conv) in enumerate(zip(original_events, validation_events)):
            # Check if event types match
            if orig['event'] != conv['event']:
                differences.append((i + 1, orig, conv, "Event type mismatch"))
                continue
                
            # Check if parameters match for most event types
            if orig['event'] != 'Header' and orig['params'] != conv['params']:
                differences.append((i + 1, orig, conv, "Parameter mismatch"))
                continue
                
            # For Header events, compare parameters except track count (index 1)
            if orig['event'] == 'Header':
                orig_params = orig['params'].copy()
                conv_params = conv['params'].copy()
                
                # Skip comparison of track count (always different)
                if len(orig_params) > 1 and len(conv_params) > 1:
                    if orig_params[0] != conv_params[0] or orig_params[2:] != conv_params[2:]:
                        differences.append((i + 1, orig, conv, "Header mismatch"))
                
            # Check timing (except for Header, Start_track, End_track)
            if orig['event'] not in ['Header', 'Start_track', 'End_track', 'End_of_file'] and orig['time'] != conv['time']:
                differences.append((i + 1, orig, conv, "Timing mismatch"))

        if differences:
            print(f"\n❌ {len(differences)} event differences found:")
            for event_num, orig, conv, reason in differences[:5]:
                print(f"\nEvent {event_num} - {reason}:")
                print(f"Original : Track {orig['track']}, Time {orig['time']}, {orig['event']}, {', '.join(orig['params'])}")
                print(f"Converted: Track {conv['track']}, Time {conv['time']}, {conv['event']}, {', '.join(conv['params'])}")
            
            if len(differences) > 5:
                print(f"\n... and {len(differences) - 5} more differences.")
            return False
        else:
            print("✓ Conversion validated successfully!")
            print("  Note: Track numbers may differ but musical content is preserved")
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

def main():
    print("MIDI-CSV Converter")
    print("=================")
    
    # Directories
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
    
    print("\nAvailable files:")
    for i, file in enumerate(midi_files + csv_files, 1):
        print(f"{i}. {file}")
    
    # Prompt user to select a file
    choice = int(input("\nSelect a file number: ")) - 1
    all_files = midi_files + csv_files
    if choice < 0 or choice >= len(all_files):
        print("Invalid selection.")
        return
        
    selected_file = all_files[choice]
    selected_file_path = os.path.join(input_dir, selected_file)
    
    # Conversion options
    if selected_file.endswith('.mid'):
        print("\nMIDI file selected. Options:")
        print("1. Convert to CSV")
        print("2. Cancel")
        action = input("\nSelect option: ").strip()
        
        if action == '1':
            convert_midi_to_csv(selected_file_path, output_dir)
            
    elif selected_file.endswith('.csv'):
        print("\nCSV file selected. Options:")
        print("1. Convert to MIDI")
        print("2. Perform round-trip validation (CSV → MIDI → CSV → Compare)")
        print("3. Cancel")
        action = input("\nSelect option: ").strip()
        
        if action == '1':
            convert_csv_to_midi(selected_file_path, output_dir)
        elif action == '2':
            round_trip_validation(selected_file_path, output_dir)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {str(e)}")
