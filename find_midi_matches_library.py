import os
import mido
import numpy as np
from match_midi_agnostic import midi_to_pitches_and_times, best_matches, format_time, split_midi
#from generate_midi import generate_midi

import logging

# Configure logging to write to stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.StreamHandler()]
)

# Create a logger
logger = logging.getLogger(__name__)

# Constants
CHUNK_LENGTH = 20  # seconds
OVERLAP = 18  # seconds

def process_directory(input_dir, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print("Converting MP3 files to MIDI files...")
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.endswith('.mp3'):
                mp3_path = os.path.join(root, file)
                midi_path = os.path.join(output_dir, os.path.splitext(file)[0] + '.mid')
                generate_midi(mp3_path, midi_path)

def load_chunks_from_directory(midi_dir):
    all_chunks = []
    all_start_times = []
    print("Chunking reference MIDI files...")
    track_names = []
    for root, _, files in os.walk(midi_dir):
        for file in files:
            if file.endswith('.mid'):
                midi_path = os.path.join(root, file)
                track_name = os.path.splitext(file)[0]
                reference_pitches, reference_times = midi_to_pitches_and_times(midi_path)
                chunks, start_times = split_midi(reference_pitches, reference_times, CHUNK_LENGTH, OVERLAP)
                all_chunks.extend(chunks)
                all_start_times.extend(start_times)
                track_names.extend([track_name] * len(chunks))
    return all_chunks, all_start_times, track_names

if __name__ == "__main__":
    #input_dir = '/content/drive/MyDrive/demucs_separated/htdemucs/'
    #output_dir = '/content/drive/MyDrive/midis/'
    output_dir = '/home/ubuntu/separated/htdemucs/midis'

    # Convert MP3 files to MIDI
    # process_directory(input_dir, output_dir)

    # Load query MIDI file
    query_midi_path = 'query.mid'  # Update this path to the actual query MIDI file
    query_pitches, query_times = midi_to_pitches_and_times(query_midi_path)

    # Load chunks from reference MIDI files
    all_chunks, all_start_times, track_names = load_chunks_from_directory(output_dir)

    # Find best matches
    logger.info("Finding the best matches using DTW...")
    top_matches = best_matches(query_pitches, all_chunks, all_start_times, track_names=track_names, top_n=10)

    # Print results
    for i, (score, start_time, shift, median_diff_semitones, track) in enumerate(top_matches):
        print(f"Match {i+1}: Score = {score}, Start time = {format_time(start_time)}, Shift = {shift} semitones, Median difference = {median_diff_semitones} Track = {track}")

    logger.info("done")


    # for i, (score, chunk, start_time, shift, median_diff_semitones) in enumerate(top_matches):
    #     print(f"Match {i+1}: Score = {score}, Start time = {format_time(start_time)}, Shift = {shift} semitones, Median difference = {median_diff_semitones} semitones")
