import mido
import numpy as np
from scipy.spatial.distance import cdist
from fastdtw import fastdtw
from tqdm import tqdm

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

# def weighted_dtw(query_pitches, reference_chunk):
#     # Calculate note duration weights
#     query_weights = np.diff(np.concatenate(([0], np.where(np.diff(query_pitches) != 0)[0] + 1, [len(query_pitches)])))
#     reference_weights = np.diff(np.concatenate(([0], np.where(np.diff(reference_chunk) != 0)[0] + 1, [len(reference_chunk)])))

#     # Calculate DTW with weights
#     distance, path = fastdtw(query_pitches, reference_chunk, dist=lambda x, y: np.abs(x - y))
    
#     # Apply weights to the distance
#     weighted_distance = sum(np.abs(query_pitches[p[0]] - reference_chunk[p[1]]) * (query_weights[p[0]] + reference_weights[p[1]]) for p in path)
#     return weighted_distance

def weighted_dtw(query_pitches, reference_chunk, use_weights=True):
    # Calculate note duration weights
    def calculate_weights(pitches):
        weights = np.diff(np.concatenate(([0], np.where(np.diff(pitches) != 0)[0] + 1, [len(pitches)])))
        return weights / weights.sum() if weights.sum() != 0 else weights

    if use_weights:
        query_weights = calculate_weights(query_pitches)
        reference_weights = calculate_weights(reference_chunk)
    else:
        query_weights = np.ones(len(query_pitches))
        reference_weights = np.ones(len(reference_chunk))

    # Calculate DTW with or without weights
    distance, path = fastdtw(query_pitches, reference_chunk, dist=lambda x, y: (x - y) ** 2)  # Using squared difference for robustness
    
    # Apply weights to the distance if use_weights is True
    if use_weights:
        weighted_distance = sum((query_pitches[p[0]] - reference_chunk[p[1]]) ** 2 * (query_weights[p[0]] + reference_weights[p[1]]) ** 1.5 for p in path)
    else:
        weighted_distance = sum((query_pitches[p[0]] - reference_chunk[p[1]]) ** 2 for p in path)
    
    return weighted_distance


def best_matches(query_pitches, reference_chunks, start_times, track_names, top_n=10):
    best_matches = []
    semitone_range = range(-1, 2)
    original_median = np.median(query_pitches)
    scores = []

    for idx, chunk in tqdm(enumerate(reference_chunks), total=len(reference_chunks)):
        if len(chunk) == 0 or np.isnan(chunk).all():
            continue
        normalized_chunk = normalize_pitch_sequence(chunk, 0)  # Normalize reference chunk by its own median
        reference_median = np.median(chunk)
        if np.isnan(reference_median):
            continue
        for shift in semitone_range:
            normalized_query = normalize_pitch_sequence(query_pitches, shift)
            distance = weighted_dtw(normalized_query, normalized_chunk)
            median_diff_semitones = (reference_median - original_median) % 12
            if track_names is None:
              track = ""
            else:
              track = track_names[idx]
            scores.append((distance, start_times[idx], shift, median_diff_semitones, track))

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
    chunk_length = 30  # seconds
    overlap = 28  # seconds

    print("Loading query MIDI file...")
    query_pitches, query_times = midi_to_pitches_and_times('query.mid')

    print("Loading reference MIDI file...")
    reference_pitches, reference_times = midi_to_pitches_and_times('reference.mid')

    print("Splitting reference MIDI file into chunks...")
    reference_chunks, start_times = split_midi(reference_pitches, reference_times, chunk_length, overlap)

    print("Finding the best matches using DTW...")
    top_matches = best_matches(query_pitches, reference_chunks, start_times, track_names=None, top_n=5)

    for i, (score, start_time, shift, median_diff_semitones, track) in enumerate(top_matches):
        print(f"Match {i+1}: Score = {score}, Start time = {format_time(start_time)}, Shift = {shift} semitones, Median difference = {median_diff_semitones} Track = {track}")
