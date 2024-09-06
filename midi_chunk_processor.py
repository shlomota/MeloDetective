import os
import mido
import numpy as np
from match_midi_agnostic import midi_to_pitches_and_times, best_matches, format_time, split_midi
import streamlit as st
import concurrent.futures
from functools import partial
from multiprocessing import Pool, cpu_count
from functools import lru_cache


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
OVERLAP = CHUNK_LENGTH - 2  # seconds

MIN_NOTES = 20  # Minimum number of notes in a chunk

def process_midi_file(midi_path, track_name, chunk_length, overlap, min_notes):
    reference_pitches, reference_times = midi_to_pitches_and_times(midi_path)
    chunks, start_times = split_midi(reference_pitches, reference_times, chunk_length, overlap)

    filtered_chunks = []
    filtered_start_times = []
    filtered_track_names = []

    for chunk, start_time in zip(chunks, start_times):
        if len(chunk) >= min_notes:
            filtered_chunks.append(chunk)
            filtered_start_times.append(start_time)
            filtered_track_names.append(track_name)

    return filtered_chunks, filtered_start_times, filtered_track_names



@st.cache_data
def load_chunks_from_directory(midi_dir):
    all_chunks = []
    all_start_times = []
    track_names = []

    logging.info("Chunking reference MIDI files...")

    midi_files = []
    for root, _, files in os.walk(midi_dir):
        for i, file in enumerate(files):
            if file.endswith('.mid'):
                midi_path = os.path.join(root, file)
                track_name = os.path.splitext(file)[0]
                midi_files.append((midi_path, track_name))

    # Define the partial function for processing each MIDI file
    process_midi_partial = partial(process_midi_file, chunk_length=CHUNK_LENGTH, overlap=OVERLAP, min_notes=MIN_NOTES)

    # Use ThreadPoolExecutor for multithreading
    #with concurrent.futures.ThreadPoolExecutor() as executor:
    #    results = list(executor.map(lambda args: process_midi_partial(*args), midi_files))

    # Use multiprocessing Pool for parallel processing
    with Pool(processes=cpu_count()) as pool:
        results = pool.starmap(process_midi_partial, midi_files)

    for chunks, start_times, track_names_chunk in results:
        all_chunks.extend(chunks)
        all_start_times.extend(start_times)
        track_names.extend(track_names_chunk)

    return all_chunks, all_start_times, track_names
