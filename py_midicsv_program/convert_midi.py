import os
import sys

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from py_midicsv.midicsv import parse as midi_to_csv

# Use the full path for input file
input_file = r"C:\ProgramData\DockerDesktop\DockerDesktopWSL\Coding\MusicMidi2\py_midicsv_program\Input\dnbshort_v9.mid"

# Convert MIDI to CSV
with open(input_file, 'rb') as midi_file:
    csv_data = midi_to_csv(midi_file)

# Write the CSV output with full path
output_file = r"C:\ProgramData\DockerDesktop\DockerDesktopWSL\Coding\MusicMidi2\py_midicsv_program\Output\dnbshort_v9.csv"
with open(output_file, 'w') as csv_file:
    csv_file.writelines(csv_data)

print(f"Converted {input_file} to {output_file}")