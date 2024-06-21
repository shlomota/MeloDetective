import torch
import torchaudio
import torchyin
import mido
from mido import MidiFile, MidiTrack, Message
from scipy.ndimage import median_filter
import pandas as pd
import numpy as np

# Constants
F_MIN = 50  # Minimum frequency (Hz)
F_MAX = 400  # Maximum frequency (Hz)
FRAME_LENGTH = 2048  # Frame length
SMOOTHING_WINDOW_SIZE = 50  # Window size for smoothing
MIN_NOTE_LENGTH = 10  # Minimum length of a note to be considered significant
REPLACEMENT_WINDOW_SIZE = 30  # Window size for averaging short notes

def smooth_pitches(pitches, window_size):
    return median_filter(pitches, size=window_size)

def replace_short_notes(pitches, min_note_length, window_size):
    smoothed_pitches = []
    current_note = None
    note_length = 0
    note_start = 0

    for i, pitch in enumerate(pitches):
        if np.isnan(pitch):
            continue

        note = int(np.round(pitch))

        if current_note is None:
            current_note = note
            note_length = 1
            note_start = i
        elif note == current_note:
            note_length += 1
        else:
            if note_length < min_note_length:
                avg_note = int(np.round(np.nanmedian(pitches[max(0, note_start-window_size//2):min(len(pitches), note_start+note_length+window_size//2)])))
                smoothed_pitches.extend([avg_note] * note_length)
            else:
                smoothed_pitches.extend([current_note] * note_length)
            current_note = note
            note_length = 1
            note_start = i

    # Ensure the last note sequence is added
    if note_length < min_note_length:
        avg_note = int(np.round(np.nanmedian(pitches[max(0, note_start-window_size//2):min(len(pitches), note_start+note_length+window_size//2)])))
        smoothed_pitches.extend([avg_note] * note_length)
    else:
        smoothed_pitches.extend([current_note] * note_length)

    return smoothed_pitches

def remove_short_notes(pitches, min_note_length):
    cleaned_pitches = []
    current_note = None
    note_length = 0

    for pitch in pitches:
        if current_note is None:
            current_note = pitch
            note_length = 1
        elif pitch == current_note:
            note_length += 1
        else:
            if note_length >= min_note_length:
                cleaned_pitches.extend([current_note] * note_length)
            current_note = pitch
            note_length = 1

    if note_length >= min_note_length:
        cleaned_pitches.extend([current_note] * note_length)

    return cleaned_pitches

def generate_midi(input_file, output_file):
    # Load the audio file
    waveform, sample_rate = torchaudio.load(input_file)

    # Move the waveform to the GPU
    waveform = waveform.to('cuda')

    # Perform pitch estimation using torch-yin
    pitch = torchyin.estimate(waveform, sample_rate=sample_rate, pitch_min=F_MIN, pitch_max=F_MAX).cpu()[0]

    # Convert to MIDI pitches (0-127)
    pitches = 69 + 12 * torch.log2(pitch / 440.0)

    # Handle inf values by replacing them with NaN
    pitches[pitches == float('inf')] = float('nan')
    pitches[pitches == float('-inf')] = float('nan')

    # Smooth the pitch sequence
    smoothed_pitches = smooth_pitches(pitches.numpy(), SMOOTHING_WINDOW_SIZE)

    # Replace NaNs with the nearest valid value using pandas
    smoothed_pitches = pd.Series(smoothed_pitches).interpolate(method='nearest').fillna(method='bfill').fillna(method='ffill').values

    # Replace short notes with the median pitch in their region
    cleaned_pitches = replace_short_notes(smoothed_pitches, MIN_NOTE_LENGTH, REPLACEMENT_WINDOW_SIZE)

    # Remove any remaining short notes
    final_pitches = remove_short_notes(cleaned_pitches, MIN_NOTE_LENGTH)

    # Calculate the original audio duration in seconds
    audio_duration = waveform.shape[1] / sample_rate

    # Create a new MIDI file and track
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)

    # Set the tempo to match the original audio duration
    ticks_per_beat = 480  # Standard MIDI resolution
    mid.ticks_per_beat = ticks_per_beat

    # Calculate the tempo in microseconds per beat
    microseconds_per_beat = (audio_duration * 1e6) / (len(final_pitches) / ticks_per_beat)
    track.append(mido.MetaMessage('set_tempo', tempo=int(microseconds_per_beat)))

    # Add MIDI note messages with timing information
    prev_note = None
    prev_time = 0

    for i, note in enumerate(final_pitches):
        if prev_note is not None and note != prev_note:
            # Add note off message for the previous note
            track.append(Message('note_off', note=int(prev_note), velocity=64, time=(i - prev_time)))
            prev_time = i
        
        # Add note on message
        if prev_note is None or note != prev_note:
            track.append(Message('note_on', note=int(note), velocity=64, time=0))
        
        prev_note = note

    # Add final note off message if there is a previous note
    if prev_note is not None:
        track.append(Message('note_off', note=int(prev_note), velocity=64, time=(len(final_pitches) - prev_time)))

    # Save the MIDI file
    mid.save(output_file)
    print(f"MIDI file saved to {output_file}")

if __name__ == "__main__":
    generate_midi('query.mp3', 'query.mid')
    generate_midi('reference.mp3', 'reference.mid')
