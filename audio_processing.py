import subprocess
import traceback
import logging
import tempfile
from pydub import AudioSegment
import os
import hashlib
import re
from download_utils import download_button
from midi_chunk_processor import best_matches, midi_to_pitches_and_times, load_chunks_from_directory
from mido import MidiFile, MidiTrack, Message
import mido
import streamlit as st
import consts
from consts import LIBRARY_DIR, MIDIS_DIR


def sanitize_filename(filename):
    """Sanitize the filename by replacing problematic characters and ensure it doesn't start with an underscore."""
    result = re.sub(r'[\\/*?:"<>|＂]', "_", filename)
    if result.startswith("_"):
        result = result[1:]
    return result


def convert_to_midi(audio_file, midi_file):
    cmd = [
        "/usr/local/bin/python2",
        "audio_to_midi_melodia/audio_to_midi_melodia.py",
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


def trim_audio(audio_segment, duration_ms=20000):
    """Trim the audio to the specified duration in milliseconds."""
    return audio_segment[:duration_ms]


def trim_midi(midi_file_path, duration=20):
    """Extract the first 20 seconds from a MIDI file."""
    try:
        midi = MidiFile(midi_file_path)
        trimmed_midi = MidiFile()

        # Get the ticks per beat from the MIDI file
        ticks_per_beat = midi.ticks_per_beat

        # Default tempo is 500000 microseconds per beat if not specified
        tempo = 500000

        for track in midi.tracks:
            new_track = MidiTrack()
            current_time = 0
            for msg in track:
                if msg.type == 'set_tempo':
                    tempo = msg.tempo

                # Convert ticks to seconds
                time_in_seconds = mido.tick2second(msg.time, ticks_per_beat, tempo)
                current_time += time_in_seconds

                if current_time <= duration:
                    new_track.append(msg)
                else:
                    break

            trimmed_midi.tracks.append(new_track)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mid") as temp_trimmed_midi:
            trimmed_midi.save(temp_trimmed_midi.name)
            return temp_trimmed_midi.name

    except Exception as e:
        print(f"Error trimming MIDI file: {e}")
        return midi_file_path


def process_audio(audio_file_path):
    if not os.path.exists(MIDIS_DIR):
        os.makedirs(MIDIS_DIR)

    # Check if the input is already a MIDI file
    file_extension = os.path.splitext(audio_file_path)[-1].lower()

    if file_extension in ['.mid', '.midi']:
        # The file is already a MIDI file, trim it to the first 20 seconds
        midi_file_path = trim_midi(audio_file_path)
    else:
        # The file is an audio file, trim it to the first 20 seconds
        audio_segment = AudioSegment.from_file(audio_file_path)
        trimmed_audio = trim_audio(audio_segment)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_trimmed_audio:
            trimmed_audio.export(temp_trimmed_audio.name, format="wav")
            trimmed_audio_path = temp_trimmed_audio.name

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mid") as temp_midi:
            midi_file_path = temp_midi.name
        try:
            convert_to_midi(trimmed_audio_path, midi_file_path)
            st.success("Audio converted to MIDI successfully!")
            download_str = download_button(open(midi_file_path, "rb").read(), "query.mid", "Download Query MIDI")
            st.markdown(download_str, unsafe_allow_html=True)
        except Exception as e:
            print(traceback.format_exc())
            print(f"Error processing audio file: {e}")
            return None, None

    try:
        # Load the query MIDI file
        query_pitches, query_times = midi_to_pitches_and_times(midi_file_path)

        # Load reference MIDI files
        all_chunks, all_start_times, track_names = load_chunks_from_directory(MIDIS_DIR)

        st.info("Finding the best matches...")

        # Find best matches
        top_n = 5
        if consts.DEBUG:
            top_n = 30
        top_matches = best_matches(query_pitches, all_chunks, all_start_times, track_names=track_names, top_n=top_n)

        return top_matches, midi_file_path
    except Exception as e:
        print(traceback.format_exc())
        print(f"Error processing MIDI file: {e}")
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
