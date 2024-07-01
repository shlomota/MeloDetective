import subprocess
import traceback
import logging
import tempfile
from pydub import AudioSegment
import os
import hashlib
import re
from download_utils import download_button
from midi_utils import midi_to_pitches_and_times
from match_midi_agnostic import best_matches
from mido import MidiFile, MidiTrack, Message
import mido
import streamlit as st
import consts
from consts import LIBRARY_DIR, MIDIS_DIR, METADATA_DIR
import shutil

    
def sanitize_filename(filename):
    """Sanitize the filename by replacing problematic characters and ensure it doesn't start with an underscore."""
    # Replace problematic characters including non-standard quotation marks
    result = re.sub(r'[\\/*?:"<>|＂]', "_", filename)

    # Ensure filename doesn't start with an underscore
    if result.startswith("_"):
        result = result[1:]

    return result

def convert_to_midi(audio_file, midi_file):
    cmd = [
        "/usr/local/bin/python2", 
        "/home/ubuntu/MeloDetective/audio_to_midi_melodia/audio_to_midi_melodia.py",
        audio_file,
        midi_file,
        "120",  # BPM, you might want to make this adjustable
        "--smooth", "0.25",
        "--minduration", "0.1"
    ]
    env = os.environ.copy()
    env.pop('PYTHONPATH', None)

    print(f"Running command: {' '.join(cmd)}")  # Debugging line
    subprocess.run(cmd, check=True, env=env)
    #subprocess.run(cmd, check=True)

def convert_to_midi(audio_file, midi_file):
    logging.info("Using basic pitch")
    with tempfile.TemporaryDirectory() as temp_dir:
        cmd = [
            "basic-pitch",  # Use the full path to basic-pitch
            "--minimum-frequency", "80",
            "--maximum-frequency", "900",
            "--onset-threshold", "0.45",
            "--minimum-note-length", "100",
            temp_dir,
            audio_file
        ]
        print(f"Running command: {' '.join(cmd)}")  # Debugging line
        subprocess.run(cmd, check=True)

        # Find the resulting MIDI file in the temporary directory
        for file_name in os.listdir(temp_dir):
            if file_name.endswith('.mid'):
                temp_midi_file = os.path.join(temp_dir, file_name)
                shutil.copy(temp_midi_file, midi_file)
                break
    logging.info("Done converting to midi with basicpitch")



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
        download_str = download_button(open(midi_file_path, "rb").read(), "query.mid", "Download Query MIDI")
        st.markdown(download_str, unsafe_allow_html=True)

        # Load the query MIDI file
        query_pitches, query_times = midi_to_pitches_and_times(midi_file_path)

        st.info("Finding the best matches...")

        # Find best matches
        top_n = 5
        if consts.DEBUG:
            top_n = 10
        top_matches = best_matches(query_pitches, top_n=top_n)

        return top_matches, midi_file_path
    except Exception as e:
        print(traceback.format_exc())
        print(f"Error processing audio file: {e}")
        return None, None

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

def split_midi(pitches, times, chunk_length=20, overlap=10):
    chunks = []
    start_times = []
    
    num_chunks = (len(times) - overlap) // (chunk_length - overlap)
    
    for i in range(num_chunks):
        start_idx = i * (chunk_length - overlap)
        end_idx = start_idx + chunk_length
        
        chunk_pitches = pitches[start_idx:end_idx]
        chunk_times = times[start_idx:end_idx]
        
        chunks.append((chunk_pitches, chunk_times))
        start_times.append(times[start_idx])
        
    return chunks, start_times

def extract_midi_chunk(midi_file_path, start_time, duration=20):
    try:
        midi = MidiFile(midi_file_path)
        chunk = MidiFile()
        for i, track in enumerate(midi.tracks):
            new_track = MidiTrack()
            current_time = 0
            for msg in track:
                current_time += msg.time
                if start_time <= current_time <= start_time + duration:
                    new_track.append(msg)
            chunk.tracks.append(new_track)
        return chunk
    except Exception as e:
        print(f"Error extracting MIDI chunk: {e}")
        return None

def extract_midi_chunk(midi_file_path, start_time, duration=20):
    try:
        midi = MidiFile(midi_file_path)
        chunk = MidiFile()

        # Get the ticks per beat from the MIDI file
        ticks_per_beat = midi.ticks_per_beat

        # Default tempo is 500000 microseconds per beat if not specified
        tempo = 500000

        for i, track in enumerate(midi.tracks):
            new_track = MidiTrack()
            current_time = 0
            for msg in track:
                if msg.type == 'set_tempo':
                    tempo = msg.tempo

                # Convert ticks to seconds
                time_in_seconds = mido.tick2second(msg.time, ticks_per_beat, tempo)
                current_time += time_in_seconds

                if start_time <= current_time <= start_time + duration:
                    new_track.append(msg)

            chunk.tracks.append(new_track)
        return chunk
    except Exception as e:
        print(f"Error extracting MIDI chunk: {e}")
        return None

def save_midi_chunk(chunk, output_path):
    try:
        chunk.save(output_path)
    except Exception as e:
        print(f"Error saving MIDI chunk: {e}")


