"""
Basic Pitch Converter Module

This module provides functions for converting audio to MIDI using Spotify's Basic Pitch.
Basic Pitch is a neural network-based pitch detection system that can convert audio to MIDI.
"""

import os
import tempfile
import numpy as np
from typing import Tuple, List, Optional, Dict, Any, Union
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Try to import basic_pitch, but provide a fallback if not available
try:
    from basic_pitch import ICASSP_2022_MODEL_PATH
    from basic_pitch.inference import predict, Model
    BASIC_PITCH_AVAILABLE = True
except ImportError:
    BASIC_PITCH_AVAILABLE = False
    print("Warning: basic_pitch not found. Install it with: pip install basic-pitch")

# Initialize the model once for reuse
basic_pitch_model = None
if BASIC_PITCH_AVAILABLE:
    try:
        basic_pitch_model = Model(ICASSP_2022_MODEL_PATH)
    except Exception as e:
        print(f"Warning: Failed to initialize Basic Pitch model: {e}")

def create_standardized_midi(midi_data, output_midi_path):
    """
    Create a standardized MIDI file from Basic Pitch outputs.
    
    Args:
        midi_data: MIDI data from Basic Pitch
        output_midi_path: Path to save the MIDI file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # First, save the original MIDI data to a temporary file
        with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as tmp_file:
            tmp_midi_path = tmp_file.name
        
        # Save the original MIDI data
        with open(tmp_midi_path, 'wb') as f:
            midi_data.write(f)
        
        # Read the MIDI file
        import mido
        midi_file = mido.MidiFile(tmp_midi_path)
        
        # Create a new MIDI file with a standardized structure
        # Use the same ticks_per_beat as the original to maintain timing
        midi = mido.MidiFile(ticks_per_beat=midi_file.ticks_per_beat)
        
        # Add a track for metadata
        meta_track = mido.MidiTrack()
        midi.tracks.append(meta_track)
        
        # Add tempo information
        meta_track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(120), time=0))
        
        # Add instrument information (Piano)
        meta_track.append(mido.MetaMessage('track_name', name='Melody', time=0))
        meta_track.append(mido.Message('program_change', program=0, time=0))
        
        # Create a track for notes
        note_track = mido.MidiTrack()
        midi.tracks.append(note_track)
        
        # Extract notes
        notes = []
        current_time = 0
        active_notes = {}
        
        for track in midi_file.tracks:
            for msg in track:
                current_time += msg.time
                
                if msg.type == 'note_on' and msg.velocity > 0:
                    # Note on - start of a note
                    active_notes[msg.note] = {
                        'onset': current_time,
                        'velocity': msg.velocity
                    }
                elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                    # Note off - end of a note
                    if msg.note in active_notes:
                        onset = active_notes[msg.note]['onset']
                        velocity = active_notes[msg.note]['velocity']
                        
                        notes.append({
                            'pitch': msg.note,
                            'onset': onset,
                            'offset': current_time,
                            'velocity': velocity
                        })
                        
                        del active_notes[msg.note]
        
        # Sort notes by onset time
        notes.sort(key=lambda x: x['onset'])
        
        # Add notes to the track
        current_time = 0
        for note in notes:
            # Calculate delta time in ticks (already in ticks, no need to multiply)
            delta_time = int(note['onset'] - current_time)
            if delta_time < 0:
                delta_time = 0
                
            # Add note_on message
            note_track.append(mido.Message('note_on', note=note['pitch'], velocity=note['velocity'], time=delta_time))
            
            # Update current time
            current_time = note['onset']
            
            # Calculate note duration in ticks (already in ticks, no need to multiply)
            duration = int(note['offset'] - note['onset'])
            if duration <= 0:
                duration = 1  # Ensure minimum duration
                
            # Add note_off message
            note_track.append(mido.Message('note_off', note=note['pitch'], velocity=0, time=duration))
            
            # Update current time
            current_time = note['offset']
        
        # Save the MIDI file
        midi.save(output_midi_path)
        
        # Clean up the temporary file
        os.unlink(tmp_midi_path)
        
        return True
    except Exception as e:
        logger.error(f"Error creating standardized MIDI file: {e}")
        return False

def convert_audio_to_midi(audio_file_path: str, output_midi_path: str, 
                         min_note_duration: float = 0.1,
                         min_frequency: float = 50.0,
                         max_frequency: float = 2000.0) -> bool:
    """
    Convert an audio file to MIDI using Basic Pitch.
    
    Args:
        audio_file_path: Path to the input audio file
        output_midi_path: Path to save the output MIDI file
        min_note_duration: Minimum note duration in seconds
        min_frequency: Minimum frequency to detect (Hz)
        max_frequency: Maximum frequency to detect (Hz)
        
    Returns:
        True if conversion was successful, False otherwise
    """
    if not BASIC_PITCH_AVAILABLE or basic_pitch_model is None:
        logger.error("Basic Pitch is not available. Please install it with: pip install basic-pitch")
        return False
    
    try:
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_midi_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # Make predictions using Basic Pitch
        model_output, midi_data, note_events = predict(
            audio_file_path,
            basic_pitch_model,
            onset_threshold=0.5,  # Adjust this threshold for note detection sensitivity
            frame_threshold=0.3,  # Adjust this threshold for pitch detection sensitivity
            minimum_note_length=min_note_duration,
            minimum_frequency=min_frequency,
            maximum_frequency=max_frequency,
            melodia_trick=True,  # Use the Melodia trick for better melody extraction
        )
        
        # Create a standardized MIDI file
        success = create_standardized_midi(midi_data, output_midi_path)
        
        # If creating a standardized MIDI file fails, try using the Basic Pitch MIDI directly
        if not success:
            # Save the MIDI file - midi_data already contains the MIDI data
            with open(output_midi_path, 'wb') as f:
                midi_data.write(f)
        
        # Verify the MIDI file was created properly
        if not os.path.exists(output_midi_path) or os.path.getsize(output_midi_path) == 0:
            logger.error(f"MIDI file was not created properly: {output_midi_path}")
            return False
        
        logger.info(f"Successfully converted {audio_file_path} to MIDI: {output_midi_path}")
        return True
    
    except Exception as e:
        logger.error(f"Error converting audio to MIDI: {e}")
        return False

def extract_notes_from_audio(audio_file_path: str) -> Union[Tuple[np.ndarray, np.ndarray], Tuple[np.ndarray, np.ndarray, str]]:
    """
    Extract notes and times from an audio file using Basic Pitch.
    
    Args:
        audio_file_path: Path to the input audio file
        
    Returns:
        Tuple of (notes, times, midi_file_path) where notes are MIDI note numbers and times are in seconds
    """
    if not BASIC_PITCH_AVAILABLE or basic_pitch_model is None:
        logger.error("Basic Pitch is not available. Please install it with: pip install basic-pitch")
        return np.array([]), np.array([])
    
    try:
        # Create a temporary MIDI file
        with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as tmp_file:
            temp_midi_path = tmp_file.name
        
        # Convert audio to MIDI
        success = convert_audio_to_midi(audio_file_path, temp_midi_path)
        if not success:
            return np.array([]), np.array([])
        
        # Extract notes from the MIDI file
        import mido
        midi_file = mido.MidiFile(temp_midi_path)
        
        notes_list = []
        times_list = []
        current_time = 0
        
        for track in midi_file.tracks:
            for msg in track:
                # Convert ticks to seconds
                current_time += msg.time / midi_file.ticks_per_beat / 2.0  # Assuming 120 BPM (2 beats per second)
                if msg.type == 'note_on' and msg.velocity > 0:
                    # Convert MIDI note to quarter tone system (multiply by 2)
                    note_value = float(msg.note * 2)  # Ensure it's a float
                    notes_list.append(note_value)
                    times_list.append(float(current_time))  # Ensure it's a float
        
        # Convert to numpy arrays
        if not notes_list:
            os.unlink(temp_midi_path)
            return np.array([]), np.array([])
            
        notes_array = np.array(notes_list, dtype=float)
        times_array = np.array(times_list, dtype=float)
        
        # Return the arrays and the MIDI path separately
        return notes_array, times_array, temp_midi_path
    
    except Exception as e:
        logger.error(f"Error extracting notes from audio: {e}")
        return np.array([]), np.array([])

if __name__ == "__main__":
    # Example usage
    if BASIC_PITCH_AVAILABLE:
        import sys
        if len(sys.argv) > 2:
            input_file = sys.argv[1]
            output_file = sys.argv[2]
            convert_audio_to_midi(input_file, output_file)
        else:
            print("Usage: python basic_pitch_converter.py input_audio.mp3 output_midi.mid")
    else:
        print("Basic Pitch is not available. Please install it with: pip install basic-pitch")