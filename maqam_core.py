"""
Maqam Core Module

This module defines the core functionality for working with Middle Eastern musical modes (maqams),
including the Maqam class and utility functions for note conversion.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from maqam_constants import (
    NOTE_NAMES, 
    MAQAM_SEMITONE_POSITIONS, 
    MAQAM_PRECISE_INTERVALS,
    MAQAM_DESCRIPTIONS,
    MAQAM_COMMON_USES
)

class Maqam:
    """
    Class representing a Middle Eastern musical mode (maqam).
    """
    def __init__(self, name: str):
        """
        Initialize a maqam with its characteristic intervals.
        
        Args:
            name: The name of the maqam (case-insensitive)
        """
        self.name = name.capitalize()
        self.name_lower = name.lower()
        
        # Get the semitone positions for this maqam
        self.semitone_positions = MAQAM_SEMITONE_POSITIONS.get(self.name_lower, [])
        
        # Get the precise intervals with quarter tones (for display only)
        self.p_intervals = MAQAM_PRECISE_INTERVALS.get(self.name_lower, [])
        
        # Get the description and common uses
        self.description = MAQAM_DESCRIPTIONS.get(self.name_lower, "")
        self.common_uses = MAQAM_COMMON_USES.get(self.name_lower, "")
        
        # Generate the scale (two octaves) starting from 0
        self.scale = self._generate_scale()
    
    def _generate_scale(self) -> List[int]:
        """
        Generate a two-octave scale from the semitone positions.
        
        Returns:
            List of note values representing the maqam scale
        """
        if not self.semitone_positions:
            return []
            
        scale = []
        
        # Generate first octave
        for pos in self.semitone_positions:
            scale.append(pos)
        
        # Generate second octave
        for pos in self.semitone_positions:
            scale.append(pos + 12)  # Add one octave
            
        return scale
    
    def get_notes_in_range(self, min_note: int, max_note: int) -> List[int]:
        """
        Get all notes of this maqam within a specific range.
        
        Args:
            min_note: Minimum note value
            max_note: Maximum note value
            
        Returns:
            List of notes within the specified range
        """
        if not self.semitone_positions:
            return []
            
        # Generate enough octaves to cover the range
        extended_scale = []
        min_octave = min_note // 12
        max_octave = max_note // 12 + 1
        
        for octave in range(min_octave, max_octave + 1):
            for pos in self.semitone_positions:
                note = octave * 12 + pos
                if min_note <= note <= max_note:
                    extended_scale.append(note)
            
        return sorted(list(set(extended_scale)))
    
    def get_scale_with_shift(self, shift: int, min_note: int, max_note: int) -> List[int]:
        """
        Get the maqam scale with a specific shift within a note range.
        
        Args:
            shift: Shift value (0-11)
            min_note: Minimum note value
            max_note: Maximum note value
            
        Returns:
            List of notes in the shifted scale within the specified range
        """
        # Generate enough octaves to cover the range
        extended_scale = []
        min_octave = min_note // 12
        max_octave = max_note // 12 + 1
        
        for octave in range(min_octave, max_octave + 1):
            for pos in self.semitone_positions:
                note = octave * 12 + pos + shift
                if min_note <= note <= max_note:
                    extended_scale.append(note)
            
        return sorted(list(set(extended_scale)))


# Dictionary of maqam objects
MAQAMS = {name: Maqam(name) for name in MAQAM_SEMITONE_POSITIONS.keys()}


def get_maqam(name: str) -> Optional[Maqam]:
    """
    Get a maqam by name.
    
    Args:
        name: Name of the maqam (case-insensitive)
        
    Returns:
        Maqam object if found, None otherwise
    """
    return MAQAMS.get(name.lower())


def get_all_maqams() -> List[Maqam]:
    """
    Get all available maqams.
    
    Returns:
        List of all maqam objects
    """
    return list(MAQAMS.values())


def frequency_to_note_value(frequency: float, reference_frequency: float = 440.0, reference_note: int = 69) -> float:
    """
    Convert a frequency to a note value with quarter tone precision.
    
    Args:
        frequency: The frequency in Hz
        reference_frequency: Reference frequency (default: A4 = 440 Hz)
        reference_note: MIDI note number of the reference frequency (default: A4 = 69)
        
    Returns:
        Note value with quarter tone precision
    """
    if frequency <= 0:
        return 0
    
    # Standard MIDI note calculation (12 semitones per octave)
    midi_note = reference_note + 12 * np.log2(frequency / reference_frequency)
    
    # Convert to quarter tone system (24 quarter tones per octave)
    quarter_tone_note = midi_note * 2
    
    return quarter_tone_note


def note_value_to_frequency(note_value: float, reference_frequency: float = 440.0, reference_note: int = 69) -> float:
    """
    Convert a note value to a frequency.
    
    Args:
        note_value: Note value with quarter tone precision
        reference_frequency: Reference frequency (default: A4 = 440 Hz)
        reference_note: MIDI note number of the reference frequency (default: A4 = 69)
        
    Returns:
        Frequency in Hz
    """
    # Convert from quarter tone system to standard MIDI note
    midi_note = note_value / 2
    
    # Convert MIDI note to frequency
    frequency = reference_frequency * 2 ** ((midi_note - reference_note) / 12)
    
    return frequency


def normalize_note_sequence(notes: List[float]) -> List[float]:
    """
    Normalize a sequence of notes by subtracting the median.
    
    Args:
        notes: List of note values
        
    Returns:
        Normalized note sequence
    """
    if len(notes) == 0:
        return []
    
    median = np.median(notes)
    return [note - median for note in notes]


def get_maqam_note_names(maqam_name: str, base_note: str = "C") -> List[str]:
    """
    Get the note names for a maqam starting from a specific base note.
    
    Args:
        maqam_name: Name of the maqam
        base_note: Base note name (default: "C")
        
    Returns:
        List of note names in the maqam
    """
    maqam = get_maqam(maqam_name)
    if not maqam:
        return []
    
    # Find base note index
    base_index = NOTE_NAMES.index(base_note) if base_note in NOTE_NAMES else 0
    
    # Generate note names for the maqam
    result = []
    
    for pos in maqam.semitone_positions:
        # Calculate the note index
        note_index = (pos + base_index) % 12
        
        # Get the note name
        note_name = NOTE_NAMES[note_index]
        result.append(note_name)
    
    return result