import mido
import numpy as np
from scipy.spatial.distance import cdist
from fastdtw import fastdtw

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

def weighted_dtw(query_pitches, reference_chunk):
    # Calculate note duration weights
    query_weights = np.diff(np.concatenate(([0], np.where(np.diff(query_pitches) != 0)[0] + 1, [len(query_pitches)])))
    reference_weights = np.diff(np.concatenate(([0], np.where(np.diff(reference_chunk) != 0)[0] + 1, [len(reference_chunk)])))

    # Calculate DTW with weights
    distance, path = fastdtw(query_pitches, reference_chunk, dist=lambda x, y: np.abs(x - y))
    
    # Apply weights to the distance
    weighted_distance = sum(np.abs(query_pitches[p[0]] - reference_chunk[p[1]]) * (query_weights[p[0]] + reference_weights[p[1]]) for p in path)
    return weighted_distance

def best_matches(query_pitches, reference_chunks, start_times, top_n=5):
    scores = []
    for idx, chunk in enumerate(reference_chunks):
        distance = weighted_dtw(query_pitches, chunk)
        scores.append((distance, chunk, start_times[idx]))

    # Sort by distance
    scores.sort(key=lambda x: x[0])
    
    # Get top N matches
    top_matches = scores[:top_n]
    return top_matches

def format_time(seconds):
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes:02}:{seconds:02}"

if __name__ == "__main__":
    chunk_length = 20  # seconds
    overlap = 19  # seconds

    print("Loading query MIDI file...")
    query_pitches, query_times = midi_to_pitches_and_times('query.mid')

    print("Loading reference MIDI file...")
    reference_pitches, reference_times = midi_to_pitches_and_times('reference.mid')
  

    print("Splitting reference MIDI file into chunks...")
    reference_chunks, start_times = split_midi(reference_pitches, reference_times, chunk_length, overlap)
    print(f"Total chunks created: {len(reference_chunks)}")

    print("Finding the best matches using DTW...")
    top_matches = best_matches(query_pitches, reference_chunks, start_times, top_n=5)

    for i, (score, chunk, start_time) in enumerate(top_matches):
        print(f"Match {i+1}: Score = {score}, Start time = {format_time(start_time)}")
