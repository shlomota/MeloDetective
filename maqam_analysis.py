"""
Maqam Analysis Module

This module provides functions for analyzing and detecting maqams in audio input.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from maqam_core import get_maqam, get_all_maqams, normalize_note_sequence
from maqam_constants import NOTE_NAMES

# Try to import scipy, but provide a fallback if not available
try:
    from scipy.spatial.distance import cosine as scipy_cosine
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    print("Warning: scipy not found. Using fallback cosine similarity implementation.")


def _cosine_similarity_fallback(v1: np.ndarray, v2: np.ndarray) -> float:
    """
    Fallback implementation of cosine similarity when scipy is not available.
    
    Args:
        v1: First vector
        v2: Second vector
        
    Returns:
        Cosine similarity (0-1, higher is more similar)
    """
    dot_product = np.dot(v1, v2)
    norm_v1 = np.sqrt(np.sum(v1 * v1))
    norm_v2 = np.sqrt(np.sum(v2 * v2))
    
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    
    return dot_product / (norm_v1 * norm_v2)


def calculate_note_histogram(notes: List[float], bin_range: Tuple[int, int] = (-24, 25), 
                        weighted: bool = False, durations: List[float] = None) -> np.ndarray:
    """
    Calculate a histogram of normalized notes.
    
    Args:
        notes: List of note values
        bin_range: Range of bins for the histogram (min, max+1)
        weighted: Whether to weight notes by their duration
        durations: List of note durations (required if weighted=True)
        
    Returns:
        Numpy array representing the histogram
    """
    if len(notes) == 0:
        return np.zeros(bin_range[1] - bin_range[0])
    
    # Normalize notes
    normalized_notes = normalize_note_sequence(notes)
    
    # Modulo to bring all notes within one octave (24 quarter tones)
    normalized_notes = [note % 24 for note in normalized_notes]
    
    # Calculate histogram
    num_bins = bin_range[1] - bin_range[0]
    if weighted and durations is not None:
        # Create weighted histogram
        histogram = np.zeros(num_bins)
        for note, duration in zip(normalized_notes, durations):
            bin_index = int(note - bin_range[0])
            if 0 <= bin_index < num_bins:
                histogram[bin_index] += duration
    else:
        # Create standard histogram
        histogram, _ = np.histogram(normalized_notes, bins=np.arange(bin_range[0], bin_range[1] + 1))
    
    # Normalize histogram
    if np.sum(histogram) > 0:
        histogram = histogram / np.sum(histogram)
    
    return histogram


def compare_histograms(hist1: np.ndarray, hist2: np.ndarray) -> float:
    """
    Compare two histograms using cosine similarity.
    
    Args:
        hist1: First histogram
        hist2: Second histogram
        
    Returns:
        Similarity score (0-1, higher is more similar)
    """
    # Handle zero histograms
    if np.sum(hist1) == 0 or np.sum(hist2) == 0:
        return 0.0
    
    if SCIPY_AVAILABLE:
        return 1 - scipy_cosine(hist1, hist2)
    else:
        return _cosine_similarity_fallback(hist1, hist2)


def calculate_maqam_accuracy_score(input_notes: List[float], maqam_scale: List[int], 
                              is_nahawand: bool = False, is_shift_9: bool = False) -> float:
    """
    Calculate an accuracy score based on how many input notes match notes in the maqam scale.
    This function directly compares the actual notes without normalization.
    Score is weighted by amplitude in the histogram.
    
    Args:
        input_notes: List of input note values
        maqam_scale: List of note values in the maqam scale
        is_nahawand: Whether this is for Nahawand maqam (for debug printing)
        is_shift_9: Whether this is for shift 9 (for debug printing)
        
    Returns:
        Accuracy score (0-1, higher is better)
    """
    if len(input_notes) == 0 or len(maqam_scale) == 0:
        return 0.0
    
    # Convert to MIDI note numbers for easier comparison
    input_midi_notes = [int(round(note / 2)) for note in input_notes]
    
    # Create a set of the maqam scale notes for efficient lookup
    maqam_notes_set = set(maqam_scale)
    
    # For debugging, also track normalized notes
    maqam_notes_normalized_set = set([note % 12 for note in maqam_scale])
    
    # Print debug info only for Nahawand at shift 9
    debug_print = is_nahawand and is_shift_9
    
    if debug_print:
        print(f"Maqam notes set (normalized): {sorted(list(maqam_notes_normalized_set))}")
        print(f"Maqam notes set (absolute, first 20): {sorted(list(maqam_notes_set))[:20]}")
    
    # Count occurrences of each note in the input (weighted by amplitude)
    note_counts = {}
    
    for note in input_midi_notes:
        if note in note_counts:
            note_counts[note] += 1
        else:
            note_counts[note] = 1
    
    # Print input notes for debugging
    if debug_print:
        print(f"Input notes (absolute): {sorted(list(note_counts.keys()))}")
        
        # For Nahawand at shift 9, print note names for better debugging
        print("\nInput notes with names:")
        for note in sorted(list(note_counts.keys())):
            note_name = NOTE_NAMES[note % 12]
            octave = note // 12 - 1  # MIDI octave convention
            print(f"  {note}: {note_name}{octave}")
            
        print("\nMaqam scale notes with names (first 20):")
        for note in sorted(list(maqam_notes_set))[:20]:
            note_name = NOTE_NAMES[note % 12]
            octave = note // 12 - 1  # MIDI octave convention
            print(f"  {note}: {note_name}{octave}")
    
    # Count matching notes (weighted by amplitude)
    matching_notes = 0
    total_notes = len(input_midi_notes)
    
    for note, count in note_counts.items():
        if note in maqam_notes_set:
            matching_notes += count
            if debug_print:
                print(f"Note {note} matched in maqam scale, count: {count}")
        elif debug_print:
            print(f"Note {note} not found in maqam scale, count: {count}")
    
    # Calculate the accuracy score - ratio of matching notes to total notes, weighted by amplitude
    accuracy = matching_notes / total_notes if total_notes > 0 else 0.0
    
    # Print detailed scores for debugging
    if debug_print:
        print(f"Matching notes: {matching_notes}/{total_notes}, Accuracy: {accuracy:.4f}")
        
        # For Nahawand at shift 9, print additional information about the scale
        if is_nahawand and is_shift_9:
            print("\nNahawand at shift 9 (A) details:")
            print("Nahawand corresponds to the natural minor scale: [0, 2, 3, 5, 7, 8, 10, 12] in semitones")
            print("When starting on A, the notes are: A, B, C, D, E, F, G, A")
            print(f"Shift value: {9}")
    
    return accuracy


def detect_maqam(notes: List[float], transposition_range: Tuple[int, int] = (-12, 13), use_semitones: bool = True) -> List[Tuple[str, float, int, float, int]]:
    """
    Detect the most likely maqam from a sequence of notes using absolute note positions.
    
    Args:
        notes: List of note values
        transposition_range: Range of transpositions to try (min, max)
        
    Returns:
        List of (maqam_name, confidence, best_shift, original_pitch, starting_note) tuples, sorted by confidence (highest first)
        where:
        - original_pitch is the estimated starting pitch of the input
        - starting_note is the actual starting note of the melody (MIDI note number)
    """
    if len(notes) == 0:
        return []
    
    # Calculate the original pitch (median) and starting note
    original_pitch = np.median(notes) if len(notes) > 0 else 0
    starting_note = int(round(min(notes) / 2)) if len(notes) > 0 else 0  # Convert to MIDI note number
    
    # Convert to MIDI note numbers for easier comparison
    input_midi_notes = [int(round(note / 2)) for note in notes]
    
    # Print debug info about the input notes
    print(f"Input notes (first 10): {notes[:10]}")
    print(f"Starting MIDI note: {starting_note}")
    print(f"Original pitch: {original_pitch}")
    print(f"Input MIDI notes: {input_midi_notes[:10]}")
    
    # Find the range of input notes
    min_midi_note = min(input_midi_notes)
    max_midi_note = max(input_midi_notes)
    
    # Compare with each maqam
    results = []
    for maqam in get_all_maqams():
        # Try different transpositions (shifts)
        best_score = 0
        best_shift = 0
        
        # Try all 12 semitone shifts
        for shift in range(0, 12, 1):
            # Generate the maqam scale with this shift
            maqam_scale = maqam.get_scale_with_shift(
                shift=shift,
                min_note=min_midi_note - 24,  # Extend range by 2 octaves below
                max_note=max_midi_note + 24   # Extend range by 2 octaves above
            )
            
            # Calculate accuracy score for this shift
            is_nahawand = (maqam.name_lower == "nahawand")
            is_shift_9 = (shift == 9)
            accuracy = calculate_maqam_accuracy_score(
                input_notes=notes,
                maqam_scale=maqam_scale,
                is_nahawand=is_nahawand,
                is_shift_9=is_shift_9
            )
            
            # Calculate the maqam's root note based on the shift
            maqam_root_index = (shift % 12)
            maqam_root_note = NOTE_NAMES[maqam_root_index]
            
            # Print detailed info ONLY for Nahawand
            if is_nahawand:
                print(f"Maqam Nahawand, Shift {shift} (starting on {maqam_root_note}): accuracy = {accuracy:.4f}")
            
            if accuracy > best_score:
                best_score = accuracy
                best_shift = shift
        
        # Include the original pitch and starting note in the results
        results.append((maqam.name_lower, best_score, best_shift, original_pitch, starting_note))
    
    # Sort by similarity (highest first)
    def sort_key(result):
        maqam_name, score, shift, original_pitch, starting_note = result
        # Primary sort: score (higher is better)
        # Secondary sort: distance from starting note (closer is better)
        starting_note_mod12 = starting_note % 12
        shift_mod12 = shift % 12
        distance = min(abs(starting_note_mod12 - shift_mod12), 
                    12 - abs(starting_note_mod12 - shift_mod12))  # Circular distance
        return (score, -distance)  # Negative distance so closer = higher priority

    results.sort(key=sort_key, reverse=True)
    
    return results