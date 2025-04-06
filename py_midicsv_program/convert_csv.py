import os
import sys

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Use the correct import path
from py_midicsv.csvmidi import parse as csv_to_midi
from py_midicsv.midi.fileio import FileWriter

input_file = "Input/dnbshort copy.csv"
output_file = "Output/dnbshort_copy.mid"

# Parse the CSV file into MIDI
with open(input_file, "r") as csv_file:
    midi_object = csv_to_midi(csv_file)

# Save the parsed MIDI file to disk
with open(output_file, "wb") as output_file:
    midi_writer = FileWriter(output_file)
    midi_writer.write(midi_object)

print(f"Converted {input_file} to {output_file}")