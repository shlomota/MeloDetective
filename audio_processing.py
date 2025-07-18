import subprocess
import traceback
import logging
import tempfile
from pydub import AudioSegment
import os
import hashlib
import re
from download_utils import download_button, download_midi_button
from midi_chunk_processor import best_matches, midi_to_pitches_and_times, load_chunks_from_directory
from mido import MidiFile, MidiTrack, Message
import mido
import streamlit as st
import consts
from consts import LIBRARY_DIR, MIDIS_DIR, METADATA_DIR
from frequency_analysis import extract_note_sequence, create_midi_from_notes
from maqam_analysis import detect_maqam
from maqam_visualization import display_maqam_results_streamlit, create_midi_player_widget

    
def sanitize_filename(filename):
    """Sanitize the filename by replacing problematic characters and ensure it doesn't start with an underscore."""
    # Replace problematic characters including non-standard quotation marks
    result = re.sub(r'[\\/*?:"<>|＂]', "_", filename)

    # Ensure filename doesn't start with an underscore
    if result.startswith("_"):
        result = result[1:]

    return result

def convert_to_midi(audio_file, midi_file):
    # Try to use Basic Pitch first, fall back to Melodia if Basic Pitch is not available
    try:
        from basic_pitch_converter import convert_audio_to_midi, BASIC_PITCH_AVAILABLE
        
        if BASIC_PITCH_AVAILABLE:
            print(f"Converting {audio_file} to MIDI using Basic Pitch")
            success = convert_audio_to_midi(audio_file, midi_file)
            if success:
                return
            else:
                print("Basic Pitch conversion failed, falling back to Melodia")
    except ImportError:
        print("Basic Pitch not available, falling back to Melodia")
    
    # Fall back to Melodia
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

def trim_audio(audio_segment, duration_ms=40000):
    """Trim the audio to the specified duration in milliseconds."""
    return audio_segment[:duration_ms]

def process_midi_file(midi_file_path):
    """
    Process MIDI file for maqam detection.
    
    Args:
        midi_file_path: Path to the MIDI file
        
    Returns:
        Tuple of (detected_maqams, midi_file_path)
    """
    try:
        # Create a progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Extract notes from MIDI file
        status_text.info("Extracting notes from MIDI file...")
        progress_bar.progress(30)
        
        # Use mido to extract notes from MIDI
        import mido
        midi_file = mido.MidiFile(midi_file_path)
        
        # Extract notes and times
        notes = []
        times = []
        current_time = 0
        
        for track in midi_file.tracks:
            for msg in track:
                current_time += msg.time
                if msg.type == 'note_on' and msg.velocity > 0:
                    # Convert MIDI note to quarter tone system (multiply by 2)
                    note_value = msg.note * 2
                    notes.append(note_value)
                    times.append(current_time)
        
        if len(notes) == 0:
            progress_bar.empty()
            status_text.error("No notes detected in the MIDI file. Please try again with a different file.")
            return None, None
        
        progress_bar.progress(60)
        
        # Provide download link for the MIDI file using our specialized MIDI download function
        download_str = download_midi_button(midi_file_path, "query.mid", "Download MIDI")
        st.markdown(download_str, unsafe_allow_html=True)
        
        # Detect maqam from the extracted notes
        status_text.info("Detecting maqam...")
        progress_bar.progress(80)
        
        # Use semitones for matching (better compatibility with Western ears)
        maqam_results = detect_maqam(notes, use_semitones=True)
        progress_bar.progress(90)
        
        # Display maqam detection results with visualization
        status_text.success("Analysis complete!")
        progress_bar.progress(100)
        
        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()
        
        # Display MIDI player with visualization
        st.subheader("MIDI Representation")
        create_midi_player_widget(midi_file_path)
        
        # Display maqam detection results
        display_maqam_results_streamlit(notes, maqam_results, midi_file_path=midi_file_path)
        
        return maqam_results, midi_file_path
    except Exception as e:
        print(traceback.format_exc())
        st.error(f"Error processing MIDI file: {e}")
        return None, None


def process_audio(audio_file_path):
    """
    Process audio file for maqam detection with enhanced quarter tone support.
    
    Args:
        audio_file_path: Path to the audio file
        
    Returns:
        Tuple of (detected_maqams, midi_file_path)
    """
    if not os.path.exists(MIDIS_DIR):
        os.makedirs(MIDIS_DIR)

    try:
        # Create a progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Try to use Basic Pitch first, fall back to frequency analysis if not available
        try:
            from basic_pitch_converter import extract_notes_from_audio, BASIC_PITCH_AVAILABLE
            
            if BASIC_PITCH_AVAILABLE:
                status_text.info("Extracting notes using Basic Pitch...")
                progress_bar.progress(10)
                
                try:
                    # Try to get notes, times, and MIDI path
                    result = extract_notes_from_audio(audio_file_path)
                    
                    if len(result) == 3:
                        notes, times, basic_pitch_midi_path = result
                    else:
                        notes, times = result
                        basic_pitch_midi_path = None
                        
                    progress_bar.progress(40)
                    
                    if len(notes) == 0:
                        status_text.warning("Basic Pitch couldn't extract notes, falling back to frequency analysis...")
                        notes, times = extract_note_sequence(audio_file_path)
                        basic_pitch_midi_path = None
                except Exception as e:
                    status_text.warning(f"Error with Basic Pitch: {e}, falling back to frequency analysis...")
                    notes, times = extract_note_sequence(audio_file_path)
                    basic_pitch_midi_path = None
            else:
                # Fall back to frequency analysis
                status_text.info("Extracting notes with frequency analysis...")
                progress_bar.progress(10)
                
                notes, times = extract_note_sequence(audio_file_path)
                progress_bar.progress(40)
        except ImportError:
            # Fall back to frequency analysis
            status_text.info("Extracting notes with frequency analysis...")
            progress_bar.progress(10)
            
            notes, times = extract_note_sequence(audio_file_path)
            progress_bar.progress(40)
        
        if len(notes) == 0:
            progress_bar.empty()
            status_text.error("No notes detected in the audio. Please try again with clearer audio.")
            return None, None
            
        # Create a MIDI file for download and visualization
        status_text.info("Creating MIDI representation...")
        progress_bar.progress(50)
        
        # Create a named temporary file that won't be deleted when closed
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mid") as temp_midi:
            midi_file_path = temp_midi.name
        
        # If we're using Basic Pitch, the MIDI file might already exist
        # Check if we have a Basic Pitch MIDI file path
        if 'basic_pitch_midi_path' in locals() and basic_pitch_midi_path and os.path.exists(basic_pitch_midi_path):
            # Copy the Basic Pitch MIDI file to our temporary file
            import shutil
            shutil.copy(basic_pitch_midi_path, midi_file_path)
            print(f"Using Basic Pitch MIDI file: {basic_pitch_midi_path}")
        else:
            # Create a MIDI file from the extracted notes
            create_midi_from_notes(notes, times, midi_file_path)
            
        progress_bar.progress(70)
        
        # Provide download link for the MIDI file using our specialized MIDI download function
        download_str = download_midi_button(midi_file_path, "query.mid", "Download MIDI")
        st.markdown(download_str, unsafe_allow_html=True)
        
        # Detect maqam from the extracted notes
        status_text.info("Detecting maqam...")
        progress_bar.progress(80)
        
        # Use semitones for matching (better compatibility with Western ears)
        maqam_results = detect_maqam(notes, use_semitones=True)
        progress_bar.progress(90)
        
        # Display maqam detection results with visualization
        status_text.success("Analysis complete!")
        progress_bar.progress(100)
        
        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()
        
        # Display MIDI player with visualization
        st.subheader("MIDI Representation")
        create_midi_player_widget(midi_file_path)
        
        # Display maqam detection results
        display_maqam_results_streamlit(notes, maqam_results, midi_file_path=midi_file_path)
        
        return maqam_results, midi_file_path
    except Exception as e:
        print(traceback.format_exc())
        st.error(f"Error processing audio file: {e}")
        return None, None

def extract_vocals(mp3_file, output_dir):
    """
    Extract vocals from an audio file using Demucs with optimized settings for maqam detection.
    
    Args:
        mp3_file: Path to the audio file
        output_dir: Directory to save the extracted vocals
        
    Returns:
        Path to the extracted vocals file
    """
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Use Demucs with optimized settings for vocal extraction
    # -n htdemucs: Use the htdemucs model which is better for vocal isolation
    # --two-stems=vocals: Only separate vocals from the rest
    # --shifts=10: Apply more shifts for better quality (default is 5)
    cmd = [
        "demucs",
        "-n", "htdemucs",
        "--two-stems=vocals",
        "--shifts=10",
        "-o", output_dir,
        mp3_file
    ]
    
    try:
        subprocess.run(cmd, check=True)
        
        # Get the filename without extension
        filename = os.path.splitext(os.path.basename(mp3_file))[0]
        
        # Path to the extracted vocals file
        vocals_path = os.path.join(output_dir, "htdemucs", filename, "vocals.wav")
        
        if os.path.exists(vocals_path):
            return vocals_path
        else:
            print(f"Vocals file not found at {vocals_path}")
            return None
    except Exception as e:
        print(f"Error extracting vocals: {e}")
        return None

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


