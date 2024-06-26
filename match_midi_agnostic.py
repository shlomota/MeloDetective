import mido
import streamlit as st
import numpy as np
from scipy.spatial.distance import cosine
from multiprocessing import Pool, cpu_count
from functools import partial
import logging
import time
import traceback
from fastdtw import fastdtw
from consts import DEBUG

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levellevel)s - %(message)s')

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

def normalize_pitch_sequence(pitches, shift=0):
    median_pitch = np.median(pitches)
    normalized_pitches = pitches - median_pitch + shift
    return normalized_pitches

def calculate_histogram(pitches, bin_range=(-20, 21)):
    histogram, _ = np.histogram(pitches, bins=np.arange(bin_range[0], bin_range[1] + 1))
    return histogram / np.sum(histogram)

def cosine_similarity(hist1, hist2):
    return 1 - cosine(hist1, hist2)

def cosine_similarity_matrix(query_hist, reference_hists):
    dot_product = np.dot(reference_hists, query_hist)
    query_norm = np.linalg.norm(query_hist)
    reference_norms = np.linalg.norm(reference_hists, axis=1)
    similarities = dot_product / (query_norm * reference_norms)
    return similarities

def weighted_dtw(query_pitches, reference_chunk, use_weights=True, reward_factor=5.0):
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
            weighted_distance += pitch_diff # * weight_sum

            if query_pitches[p[0]] == reference_chunk[p[1]]:
                weighted_distance -= reward_factor * weight_sum

    except IndexError as e:
        return float('inf')

    return weighted_distance

def process_chunk_cosine(chunk_data, query_hist, semitone_range):
    try:
        idx, chunk, start_time, track_name = chunk_data
        if len(chunk) == 0 or np.isnan(chunk).all():
            return None

        best_similarity = -1
        best_shift = 0
        median_diff_semitones = 0

        for shift in range(*semitone_range):
            normalized_chunk = normalize_pitch_sequence(chunk, shift)
            chunk_hist = calculate_histogram(normalized_chunk)
            similarity = cosine_similarity(query_hist, chunk_hist)

            if similarity > best_similarity:
                best_similarity = similarity
                best_shift = shift
                median_diff_semitones = int(np.median(chunk) - np.median(query_hist))

        return (best_similarity, start_time, best_shift, median_diff_semitones, track_name, idx)
    except Exception as e:
        logging.error("Error in process_chunk_cosine: %s", traceback.format_exc())
        return None

def process_chunk_cosine_matrix_batch(query_hist, reference_chunks, chunk_data, start_times, track_names):
    reference_hists = []
    for idx, shift in chunk_data:
        chunk = reference_chunks[idx]
        if len(chunk) == 0 or np.isnan(chunk).all():
            continue
        normalized_chunk = normalize_pitch_sequence(chunk, shift)
        chunk_hist = calculate_histogram(normalized_chunk)
        reference_hists.append(chunk_hist)
    reference_hists = np.array(reference_hists)
    similarities = cosine_similarity_matrix(query_hist, reference_hists)
    results = []
    for ((idx, shift), similarity) in zip(chunk_data, similarities):
        median_diff_semitones = int(np.median(reference_chunks[idx]) - np.median(query_hist))
        track_name = track_names[idx]
        start_time = start_times[idx]
        results.append((similarity, start_time, shift, median_diff_semitones, track_name, idx))
    return results

def best_matches_cosine(query_pitches, reference_chunks, start_times, track_names, top_n=100):
    start = time.time()
    normalized_query_pitches = normalize_pitch_sequence(query_pitches)
    query_hist = calculate_histogram(normalized_query_pitches)

    chunk_data = [(idx, shift) for idx in range(len(reference_chunks)) for shift in range(-1, 2)]
    batch_size = len(chunk_data) // cpu_count()  # Divide work into batches
    chunk_batches = [chunk_data[i:i + batch_size] for i in range(0, len(chunk_data), batch_size)]

    with Pool(processes=cpu_count()) as pool:
        results = pool.starmap(process_chunk_cosine_matrix_batch, [(query_hist, reference_chunks, batch, start_times, track_names) for batch in chunk_batches])

    end = time.time()
    if DEBUG:
        st.text("%s" % (end - start))
    # Flatten results
    results = [item for sublist in results for item in sublist]
    scores = sorted(results, key=lambda x: x[0], reverse=True)  # Higher similarity is better

    return scores[:top_n]


def process_chunk_dtw(chunk_data, query_pitches, reference_chunks):
    try:
        cosine_similarity_score, start_time, best_shift, median_diff_semitones, track_name, idx = chunk_data
        chunk = reference_chunks[idx]
        if len(chunk) == 0 or np.isnan(chunk).all():
            return None

        normalized_chunk = normalize_pitch_sequence(chunk, 0)
        reference_median = np.median(chunk)
        if np.isnan(reference_median):
            return None
        original_median = np.median(query_pitches)
        median_diff_semitones = int(reference_median - original_median)

        best_score = float('inf')
        for shift in range(-1, 2):
            normalized_query = normalize_pitch_sequence(query_pitches, shift)
            distance = weighted_dtw(normalized_query, normalized_chunk)
            if distance < best_score:
                best_score = distance
                best_shift = shift

        return (cosine_similarity_score, best_score, start_time, best_shift, median_diff_semitones, track_name)
    except Exception as e:
        logging.error("Error in process_chunk_dtw: %s", traceback.format_exc())
        return None

def best_matches(query_pitches, reference_chunks, start_times, track_names, top_n=10):
    # Step 1: Prefilter with Cosine Similarity
    logging.info("Starting prefiltering with cosine similarity...")
    top_cosine_matches = best_matches_cosine(query_pitches, reference_chunks, start_times, track_names, top_n=500)

    # Step 2: Rerank with DTW
    logging.info("Starting reranking with DTW...")
    start = time.time()
    process_chunk_partial = partial(process_chunk_dtw, query_pitches=query_pitches, reference_chunks=reference_chunks)

    final_results = [process_chunk_partial(match) for match in top_cosine_matches]
    end = time.time()
    if DEBUG:
        st.text("DTW took %s seconds" % (end - start))

    final_scores = [result for result in final_results if result is not None]
    final_scores.sort(key=lambda x: x[1])  # Lower DTW score is better

    # Ensure unique tracks in final results
    unique_tracks = set()
    final_scores = [match for match in final_scores if match[5] not in unique_tracks and not unique_tracks.add(match[5])]

    logging.info("Final top matches after DTW: %s", final_scores[:top_n])
    return final_scores[:top_n]

def format_time(seconds):
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes:02}:{seconds:02}"

if __name__ == "__main__":
    chunk_length = 20  # seconds
    overlap = 18  # seconds

    try:
        logging.info("Loading query MIDI file...")
        query_pitches, query_times = midi_to_pitches_and_times('query.mid')

        logging.info("Loading reference MIDI file...")
        reference_pitches, reference_times = midi_to_pitches_and_times('reference.mid')

        logging.info("Splitting reference MIDI file into chunks...")
        reference_chunks, start_times = split_midi(reference_pitches, reference_times, chunk_length, overlap)

        logging.info("Finding the best matches using histogram comparison and DTW...")
        track_names = ["Track" + str(i) for i in range(len(reference_chunks))]
        top_matches = best_matches(query_pitches, reference_chunks, start_times, track_names, top_n=10)

        for i, (cosine_similarity_score, dtw_score, start_time, shift, median_diff_semitones, track) in enumerate(top_matches):
            logging.info(f"Match {i+1}: Cosine Similarity = {cosine_similarity_score:.2f}, DTW Score = {dtw_score:.2f}, Start time = {format_time(start_time)}, Shift = {shift} semitones, Median difference = {median_diff_semitones} semitones, Track Name = {track}")

    except Exception as e:
        logging.error("Error processing sample query: %s", traceback.format_exc())
        st.error(f"Error processing sample query: {e}")

