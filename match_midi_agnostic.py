import mido
import streamlit as st
import numpy as np
from scipy.spatial.distance import cosine
from multiprocessing import Pool, cpu_count
import multiprocessing
from functools import partial
import logging
import time
import traceback
from fastdtw import fastdtw
import consts
from consts import CHROMA_CLIENT, MIDIS_COLLECTION
import concurrent.futures


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


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

def weighted_dtw(query_pitches, reference_chunk, stretch_penalty=0.2, threshold=5*10):
    distance, path = fastdtw(query_pitches, reference_chunk, dist=lambda x, y: (x - y) ** 2)
    total_distance = distance
    stretch_length = 0
    path_length = len(path)

    for i in range(1, path_length):
        prev = path[i-1]
        curr = path[i]
        if curr[0] == prev[0] or curr[1] == prev[1]:  # Horizontal or vertical step
            stretch_length += 1
        else:
            if stretch_length > 0:
                # Apply reduced penalty at the start and end of the path
                if i <= threshold or i >= path_length - threshold:
                    total_distance += (stretch_length ** 2) * (stretch_penalty / 5)
                else:
                    total_distance += (stretch_length ** 2) * stretch_penalty
                stretch_length = 0
    if stretch_length > 0:
        # Apply reduced penalty at the end of the path
        if path_length - stretch_length <= threshold:
            total_distance += (stretch_length ** 2) * (stretch_penalty / 2)
        else:
            total_distance += (stretch_length ** 2) * stretch_penalty
    return total_distance, path

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


def process_chunk_dtw(chunk_data, query_pitches, reference_chunks):
    try:
        cosine_similarity_score, note_sequence, start_time, histogram_vector, idx, track_name = chunk_data
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
        best_path = None
        best_shift = 0
        for shift in range(-1, 2):
            normalized_query = normalize_pitch_sequence(query_pitches, shift)
            distance, path = weighted_dtw(normalized_query, normalized_chunk)
            if distance < best_score:
                best_score = distance
                best_shift = shift
                best_path = path

        return (cosine_similarity_score, best_score, start_time, best_shift, best_path, median_diff_semitones, track_name)
    except Exception as e:
        logging.error(f"Error in process_chunk_dtw: {traceback.format_exc()}")
        return None

def best_matches(query_pitches, top_n=10):
    logging.info("Starting prefiltering with cosine similarity...")

    # Generate shifted queries
    shifted_queries = [normalize_pitch_sequence(query_pitches, shift) for shift in range(-2, 3)]
    shifted_hists = [calculate_histogram(shifted_query) for shifted_query in shifted_queries]

    # Query ChromaDB for each shifted histogram
    all_results = []
    for hist in shifted_hists:
        query_result = MIDIS_COLLECTION.query(
            query_embeddings=[hist.tolist()],
            n_results=top_n * 100  # Retrieve more for DTW re-ranking
        )
        logging.info(f"Query result keys: {query_result.keys()}")
        logging.info(f"Query distances sample: {query_result['distances'][0][:5]}")

        for i in range(len(query_result["documents"][0])):
            try:
                metadata = query_result["metadatas"][0][i]
                similarity = 1 - query_result["distances"][0][i]
                note_sequence = np.array(list(map(int, metadata["note_sequence"].split(','))))
                histogram_vector = np.array(list(map(float, metadata["histogram_vector"].split(','))))
                start_time = metadata["start_time"]
                track_name = metadata["track_name"]
                all_results.append((similarity, note_sequence, start_time, histogram_vector, i, track_name))
            except (ValueError, TypeError) as e:
                logging.error(f"Error parsing metadata for document {i}: {e}")
                logging.error(f"Metadata content: {metadata}")

    if not all_results:
        logging.error("No valid results found in ChromaDB query.")
        return []

    # Sort results by cosine similarity
    all_results.sort(key=lambda x: x[0], reverse=True)
    top_cosine_matches = all_results[:top_n * 100]

    # Rerank with DTW using multithreading
    logging.info("Starting reranking with DTW...")
    start = time.time()

    process_chunk_partial = partial(process_chunk_dtw, query_pitches=query_pitches, reference_chunks=[result[1] for result in top_cosine_matches])

    with concurrent.futures.ThreadPoolExecutor() as executor:
        final_results = list(executor.map(process_chunk_partial, top_cosine_matches))

    end = time.time()
    if consts.DEBUG:
        st.text(f"DTW took {end - start} seconds, on {len(top_cosine_matches)} items")

    final_scores = [result for result in final_results if result is not None]
    final_scores.sort(key=lambda x: x[1])  # Lower DTW score is better

    # Deduplicate results
    seen_tracks = set()
    unique_final_scores = []
    for score in final_scores:
        track_name = score[-1]
        if track_name not in seen_tracks:
            unique_final_scores.append(score)
            seen_tracks.add(track_name)
        if len(unique_final_scores) == top_n:
            break

    logging.info("Final top matches after DTW: %s", unique_final_scores)
    return unique_final_scores


def format_time(seconds):
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes:02}:{seconds:02}"

