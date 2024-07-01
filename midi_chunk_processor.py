import os
import mido
import numpy as np
from match_midi_agnostic import midi_to_pitches_and_times, split_midi, calculate_histogram
import logging
from multiprocessing import Pool, cpu_count
import chromadb
from functools import partial
from consts import MIDIS_DIR, CHROMA_CLIENT, MIDIS_COLLECTION
# Constants
CHUNK_LENGTH = 20  # seconds
OVERLAP = 18.5  # seconds
MIN_NOTES = 20  # Minimum number of notes in a chunk

def process_midi_file(midi_path, track_name, chunk_length, overlap, min_notes):
    reference_pitches, reference_times = midi_to_pitches_and_times(midi_path)
    chunks, start_times = split_midi(reference_pitches, reference_times, chunk_length, overlap)

    filtered_chunks = []
    filtered_start_times = []
    filtered_track_names = []
    histograms = []

    for chunk, start_time in zip(chunks, start_times):
        if len(chunk) >= min_notes:
            filtered_chunks.append(chunk)
            filtered_start_times.append(start_time)
            filtered_track_names.append(track_name)
            histogram = calculate_histogram(chunk)
            histograms.append(histogram)

    return filtered_chunks, filtered_start_times, filtered_track_names, histograms

def add_midi_to_chromadb(midi_file_path, track_name):
    chunks, start_times, track_names, histograms = process_midi_file(midi_file_path, track_name, CHUNK_LENGTH, OVERLAP, MIN_NOTES)
    for chunk, start_time, histogram in zip(chunks, start_times, histograms):
        chunk_id = f"{track_name}_{start_time}"
        MIDIS_COLLECTION.add_document(
            chunk_id,
            {
                "track_name": track_name,
                "start_time": start_time,
                "chunk_length": CHUNK_LENGTH,
                "note_sequence": chunk.tolist(),
                "histogram_vector": histogram.tolist()
            }
        )

def load_chunks_to_chromadb(midi_dir):
    midi_files = []
    for root, _, files in os.walk(midi_dir):
        for file in files:
            if file.endswith('.mid'):
                midi_path = os.path.join(root, file)
                track_name = os.path.splitext(file)[0]
                midi_files.append((midi_path, track_name))

    process_midi_partial = partial(process_midi_file, chunk_length=CHUNK_LENGTH, overlap=OVERLAP, min_notes=MIN_NOTES)

    with Pool(processes=cpu_count()) as pool:
        results = pool.starmap(process_midi_partial, midi_files)

    for chunks, start_times, track_names_chunk, histograms in results:
        for chunk, start_time, track_name, histogram in zip(chunks, start_times, track_names_chunk, histograms):
            chunk_id = f"{track_name}_{start_time}"
            MIDIS_COLLECTION.add_document(
                chunk_id,
                {
                    "track_name": track_name,
                    "start_time": start_time,
                    "chunk_length": CHUNK_LENGTH,
                    "note_sequence": chunk.tolist(),
                    "histogram_vector": histogram.tolist()
                }
            )

if __name__ == "__main__":
    midi_dir = MIDIS_DIR
    load_chunks_to_chromadb(midi_dir)
