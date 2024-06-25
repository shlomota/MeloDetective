import mido
import streamlit as st
import numpy as np
from scipy.spatial.distance import cdist
from fastdtw import fastdtw
from tqdm import tqdm
from multiprocessing import Pool, cpu_count
from functools import partial
import logging
import time

def midi_to_pitches_and_times(midi_file):
    midi = mido.MidiFile(midi_file)
    pitches = []
    times = []
    time = 0
    for msg in midi:
        time += msg.time
        if msg.type == 'note_on' and msg.velocity > 0:
            pitches.append(msg.note)
            times.append(time)
    return np.array(pitches), np.array(times)

def split_midi(pitches, times, chunk_length, overlap):
    chunks = []
    start_times = []
    num_chunks = int((times[-1] - chunk_length) // (chunk_length - overlap)) + 1
    for i in range(num_chunks):
        start_time = i * (chunk_length - overlap)
        end_time = start_time + chunk_length
        indices = np.where((times >= start_time) & (times < end_time))
        chunk_pitches = pitches[indices]
        chunks.append(chunk_pitches)
        start_times.append(start_time)
    return chunks, start_times

def normalize_pitch_sequence(pitches, shift):
    median_pitch = np.median(pitches)
    normalized_pitches = pitches - median_pitch + shift
    return normalized_pitches

def weighted_dtw(query_pitches, reference_chunk, use_weights=True, reward_factor=5.0):
    # Calculate note duration weights
    def calculate_weights(pitches):
        change_points = np.concatenate(([0], np.where(np.diff(pitches) != 0)[0] + 1, [len(pitches)]))
        weights = np.diff(change_points)
        expanded_weights = np.repeat(weights, weights)
        return expanded_weights / expanded_weights.sum() if expanded_weights.sum() != 0 else np.ones(len(pitches))

    if use_weights:
        query_weights = calculate_weights(query_pitches)
        reference_weights = calculate_weights(reference_chunk)
    else:
        query_weights = np.ones(len(query_pitches))
        reference_weights = np.ones(len(reference_chunk))

    try:
        distance, path = fastdtw(query_pitches, reference_chunk, dist=lambda x, y: (x - y) ** 2)

        weighted_distance = 0
        for p in path:
            pitch_diff = (query_pitches[p[0]] - reference_chunk[p[1]]) ** 2
            weight_sum = query_weights[p[0]] + reference_weights[p[1]]
            if False and use_weights:
                weighted_distance += pitch_diff * weight_sum
            else:
                weighted_distance += pitch_diff

            # Positive reward for matching long notes
            if query_pitches[p[0]] == reference_chunk[p[1]]:
                #weighted_distance -= reward_factor * ((weight_sum / 2) ** 0.5)
                weighted_distance -= reward_factor * weight_sum

    except IndexError as e:
        return float('inf')

    return weighted_distance

def process_chunk(chunk_data, query_pitches, semitone_range):
    idx, chunk, start_time, track_name = chunk_data
    if len(chunk) == 0 or np.isnan(chunk).all():
        return None
    normalized_chunk = normalize_pitch_sequence(chunk, 0)
    reference_median = np.median(chunk)
    if np.isnan(reference_median):
        return None
    original_median = np.median(query_pitches)
    median_diff_semitones = int(reference_median - original_median)

    best_score = float('inf')
    best_shift = 0
    for shift in semitone_range:
        normalized_query = normalize_pitch_sequence(query_pitches, shift)
        distance = weighted_dtw(normalized_query, normalized_chunk)
        if distance < best_score:
            best_score = distance
            best_shift = shift

    return (best_score, start_time, best_shift, median_diff_semitones, track_name)

def best_matches(query_pitches, reference_chunks, start_times, track_names, top_n=10):
    semitone_range = range(-1, 2)
    chunk_data = zip(range(len(reference_chunks)), reference_chunks, start_times, track_names)

    process_chunk_partial = partial(process_chunk, query_pitches=query_pitches, semitone_range=semitone_range)

    start = time.time()
    num_processes = cpu_count()
    logging.info("finding matches with %s processes" % (num_processes))

    with Pool(processes=num_processes) as pool:
        results = pool.map(process_chunk_partial, chunk_data)

    logging.info("found matches with %s processes" % (num_processes))
    end = time.time()
    st.text("%s" % (end - start))

    scores = [result for result in results if result is not None]
    scores.sort(key=lambda x: x[0])

    unique_matches = []
    seen_tracks = set()
    for match in scores:
        if match[4] not in seen_tracks:
            unique_matches.append(match)
            seen_tracks.add(match[4])
        if len(unique_matches) == top_n:
            break

    return unique_matches

def format_time(seconds):
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes:02}:{seconds:02}"

if __name__ == "__main__":
    chunk_length = 20  # seconds
    overlap = 18  # seconds

    print("Loading query MIDI file...")
    query_pitches, query_times = midi_to_pitches_and_times('query.mid')

    print("Loading reference MIDI file...")
    reference_pitches, reference_times = midi_to_pitches_and_times('reference.mid')

    print("Splitting reference MIDI file into chunks...")
    reference_chunks, start_times = split_midi(reference_pitches, reference_times, chunk_length, overlap)

    print("Finding the best matches using DTW...")
    top_matches = best_matches(query_pitches, reference_chunks, start_times, track_names=None, top_n=10)

    for i, (score, start_time, shift, median_diff_semitones, track) in enumerate(top_matches):
        print(f"Match {i+1}: Score = {score}, Start time = {format_time(start_time)}, Shift = {shift} semitones, Median difference = {median_diff_semitones} Track = {track}")
