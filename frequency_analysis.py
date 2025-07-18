"""
Frequency Analysis Module

This module provides enhanced frequency extraction capabilities for detecting quarter tones
in audio recordings. It extends the existing audio processing pipeline with higher resolution
frequency analysis and improved note conversion.
"""

import numpy as np
import librosa
import soundfile as sf
import tempfile
from typing import List, Tuple, Dict, Optional, Union
from maqam_definitions import frequency_to_note_value, note_value_to_frequency
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants for frequency analysis
DEFAULT_SR = 44100  # Default sample rate
HOP_LENGTH = 128    # Hop length for pitch detection (smaller for better time resolution)
FMIN = 65.0         # Minimum frequency in Hz (C2)
FMAX = 1000.0       # Maximum frequency in Hz (B5)
FRAME_LENGTH = 2048 # Frame length for pitch detection


def extract_frequencies(audio_file: str, sr: int = DEFAULT_SR) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Extract frequency information from an audio file with high resolution for quarter tone detection.
    
    Args:
        audio_file: Path to the audio file
        sr: Sample rate for analysis
        
    Returns:
        Tuple of (frequencies, times, confidence)
    """
    try:
        # Load the audio file
        y, sr = librosa.load(audio_file, sr=sr, mono=True)
        
        # Extract pitch using pYIN algorithm (more accurate for monophonic audio)
        # This gives better quarter tone resolution than basic pitch tracking
        f0, voiced_flag, voiced_probs = librosa.pyin(
            y, 
            fmin=FMIN,
            fmax=FMAX,
            sr=sr,
            hop_length=HOP_LENGTH,
            frame_length=FRAME_LENGTH
        )
        
        # Get time values for each frame
        times = librosa.times_like(f0, sr=sr, hop_length=HOP_LENGTH)
        
        # Filter out unvoiced frames and low confidence detections
        confidence_threshold = 0.4
        mask = (voiced_flag) & (voiced_probs >= confidence_threshold)
        
        frequencies = f0[mask]
        filtered_times = times[mask]
        confidence = voiced_probs[mask]
        
        logger.info(f"Extracted {len(frequencies)} frequency points from audio")
        
        return frequencies, filtered_times, confidence
        
    except Exception as e:
        logger.error(f"Error extracting frequencies: {e}")
        return np.array([]), np.array([]), np.array([])


def frequencies_to_notes(frequencies: np.ndarray, times: np.ndarray, confidence: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Convert frequencies to note values with quarter tone precision.
    
    Args:
        frequencies: Array of frequency values in Hz
        times: Array of time points for each frequency
        confidence: Array of confidence values for each frequency
        
    Returns:
        Tuple of (notes, times, confidence)
    """
    if len(frequencies) == 0:
        return np.array([]), times, confidence
    
    # Convert frequencies to note values
    notes = np.array([frequency_to_note_value(freq) for freq in frequencies])
    
    return notes, times, confidence


def smooth_notes(notes: np.ndarray, times: np.ndarray, confidence: np.ndarray, 
                window_size: int = 5, min_confidence: float = 0.8) -> Tuple[np.ndarray, np.ndarray]:
    """
    Apply smoothing to the note sequence to reduce noise and improve stability.
    
    Args:
        notes: Array of note values
        times: Array of time points
        confidence: Array of confidence values
        window_size: Size of the smoothing window
        min_confidence: Minimum confidence threshold
        
    Returns:
        Tuple of (smoothed_notes, times)
    """
    if len(notes) <= window_size:
        return notes, times
    
    smoothed_notes = np.copy(notes)
    
    # Apply median filtering to reduce outliers
    for i in range(window_size, len(notes) - window_size):
        window = notes[i-window_size:i+window_size+1]
        conf_window = confidence[i-window_size:i+window_size+1]
        
        # Only consider high confidence values for smoothing
        high_conf_indices = conf_window >= min_confidence
        if np.any(high_conf_indices):
            high_conf_window = window[high_conf_indices]
            smoothed_notes[i] = np.median(high_conf_window)
    
    return smoothed_notes, times


def quantize_to_quarter_tones(notes: np.ndarray) -> np.ndarray:
    """
    Quantize note values to the nearest quarter tone.
    
    Args:
        notes: Array of note values
        
    Returns:
        Array of quantized note values
    """
    # Round to nearest quarter tone (0.5 units in our system)
    return np.round(notes * 2) / 2


def extract_note_sequence(audio_file: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Extract a sequence of notes with quarter tone precision from an audio file.
    
    Args:
        audio_file: Path to the audio file
        
    Returns:
        Tuple of (notes, times)
    """
    # Extract frequencies
    frequencies, times, confidence = extract_frequencies(audio_file)
    
    if len(frequencies) == 0:
        logger.warning("No frequencies detected in the audio file")
        return np.array([]), np.array([])
    
    # Convert to notes
    notes, times, confidence = frequencies_to_notes(frequencies, times, confidence)
    
    # Smooth the note sequence
    smoothed_notes, times = smooth_notes(notes, times, confidence)
    
    # Quantize to quarter tones
    quantized_notes = quantize_to_quarter_tones(smoothed_notes)
    
    return quantized_notes, times


def create_midi_from_notes(notes: np.ndarray, times: np.ndarray, output_file: str) -> bool:
    """
    Create a MIDI file from a sequence of notes with quarter tone support.
    
    Args:
        notes: Array of note values
        times: Array of time points
        output_file: Path to the output MIDI file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        import mido
        from mido import Message, MidiFile, MidiTrack, MetaMessage
        
        # Create a new MIDI file with one track
        mid = MidiFile(ticks_per_beat=480)
        track = MidiTrack()
        mid.tracks.append(track)
        
        # Add tempo information
        tempo = mido.bpm2tempo(120)  # 120 BPM
        track.append(MetaMessage('set_tempo', tempo=tempo, time=0))
        
        # Convert note values to MIDI notes
        # For quarter tones, we'll round to the nearest semitone for MIDI compatibility
        # but we'll adjust the pitch bend to achieve quarter tone precision
        midi_notes = np.round(notes / 2).astype(int)  # Convert to standard MIDI notes
        
        # Calculate pitch bend values for quarter tones
        # MIDI pitch bend range is typically ±2 semitones with 8192 as the center (no bend)
        # So for quarter tones, we need to use pitch bend values of ±2048
        pitch_bends = np.round((notes / 2 - midi_notes) * 4096).astype(int)
        
        # Calculate note durations
        if len(times) <= 1:
            return False
            
        durations = np.diff(times, append=times[-1] + 0.25)  # Add a small duration for the last note
        
        # Convert times to ticks
        ticks_per_second = mid.ticks_per_beat * 2  # Assuming 120 BPM (2 beats per second)
        tick_times = np.round(times * ticks_per_second).astype(int)
        tick_durations = np.round(durations * ticks_per_second).astype(int)
        
        # Add notes to the track
        last_time = 0
        for i in range(len(midi_notes)):
            # Calculate delta time
            delta_time = tick_times[i] - last_time
            last_time = tick_times[i]
            
            # Set pitch bend for quarter tone precision
            if abs(pitch_bends[i]) > 0:
                track.append(Message('pitchwheel', pitch=pitch_bends[i], time=delta_time))
                delta_time = 0  # Reset delta time for the note_on message
            
            # Add note_on message
            track.append(Message('note_on', note=midi_notes[i], velocity=64, time=delta_time))
            
            # Add note_off message
            track.append(Message('note_off', note=midi_notes[i], velocity=0, time=tick_durations[i]))
            
            # Reset pitch bend after the note
            if abs(pitch_bends[i]) > 0:
                track.append(Message('pitchwheel', pitch=0, time=0))
        
        # Save the MIDI file
        mid.save(output_file)
        logger.info(f"MIDI file saved to {output_file}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error creating MIDI file: {e}")
        return False


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        audio_file = sys.argv[1]
        print(f"Processing audio file: {audio_file}")
        
        notes, times = extract_note_sequence(audio_file)
        
        print(f"Extracted {len(notes)} notes")
        if len(notes) > 0:
            print(f"First 10 notes: {notes[:10]}")
            print(f"First 10 times: {times[:10]}")
            
            # Create a MIDI file
            output_midi = "output.mid"
            success = create_midi_from_notes(notes, times, output_midi)
            
            if success:
                print(f"MIDI file created: {output_midi}")
            else:
                print("Failed to create MIDI file")
    else:
        print("Please provide an audio file path")