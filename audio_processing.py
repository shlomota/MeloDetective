import subprocess
import tempfile
from pydub import AudioSegment
import os
import streamlit as st
import hashlib
import yt_dlp
import re
from find_midi_matches_library import best_matches, midi_to_pitches_and_times, load_chunks_from_directory

LIBRARY_DIR = "data/library"
MIDIS_DIR = "data/midis"
METADATA_DIR = "data/metadata"

def sanitize_filename(filename):
    """Sanitize the filename by replacing problematic characters."""
    return re.sub(r'[\\/*?:"<>|]', "_", filename)

def convert_to_midi(audio_file, midi_file):
    cmd = [
        "python2", 
        "audio_to_midi_melodia/audio_to_midi_melodia.py",
        audio_file,
        midi_file,
        "120",  # BPM, you might want to make this adjustable
        "--smooth", "0.25",
        "--minduration", "0.1"
    ]
    print(f"Running command: {' '.join(cmd)}")  # Debugging line
    subprocess.run(cmd, check=True)

def trim_audio(audio_segment, duration_ms=20000):
    """Trim the audio to the specified duration in milliseconds."""
    return audio_segment[:duration_ms]

def process_audio(audio_file_path):
    if not os.path.exists(MIDIS_DIR):
        os.makedirs(MIDIS_DIR)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mid") as temp_midi:
        midi_file_path = temp_midi.name

    try:
        convert_to_midi(audio_file_path, midi_file_path)
        st.success("Audio converted to MIDI successfully!")

        # Load the query MIDI file
        query_pitches, query_times = midi_to_pitches_and_times(midi_file_path)
        
        # Load reference MIDI files
        all_chunks, all_start_times, track_names = load_chunks_from_directory(MIDIS_DIR)

        # Find best matches
        st.info("Finding the best matches using DTW...")
        top_matches = best_matches(query_pitches, all_chunks, all_start_times, track_names=track_names, top_n=3)

        return top_matches
    except Exception as e:
        st.error(f"Error processing audio file: {e}")
        return None
    finally:
        os.unlink(midi_file_path)

def extract_vocals(mp3_file, output_dir):
    cmd = [
        "demucs",
        "-o", output_dir,
        mp3_file
    ]
    subprocess.run(cmd, check=True)
    
def is_in_library(query):
    query_hash = hashlib.md5(query.encode()).hexdigest()
    midi_file = os.path.join(MIDIS_DIR, f"{query_hash}.mid")
    return os.path.exists(midi_file)

