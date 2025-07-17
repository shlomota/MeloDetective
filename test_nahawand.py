"""
Quick script to test the exact input notes against Nahawand maqam at shift 9 (starting on A)
without any normalization.
"""

import numpy as np
from typing import List, Set

def generate_nahawand_scale(shift: int = 9, starting_midi_note: int = 57) -> List[int]:
    """
    Generate a Nahawand scale with the specified shift.
    
    Args:
        shift: The shift value (0-11)
        starting_midi_note: The MIDI note number of the starting note
        
    Returns:
        List of MIDI note numbers in the Nahawand scale
    """
    # The correct semitone positions for Nahawand (natural minor scale)
    semitone_positions = [0, 2, 3, 5, 7, 8, 10]
    
    # Generate 5 octaves of the maqam scale centered around the starting note
    maqam_scale = []
    
    # Find the range of input notes
    min_midi_note = starting_midi_note
    max_midi_note = starting_midi_note + 12  # One octave above
    
    # Extend the range by 2 octaves in each direction
    min_octave = (min_midi_note // 12) - 2
    max_octave = (max_midi_note // 12) + 2
    
    # Generate the maqam scale across this range
    for octave in range(min_octave, max_octave + 1):
        for pos in semitone_positions:
            note = octave * 12 + pos + shift
            maqam_scale.append(note)
    
    return sorted(maqam_scale)

def test_nahawand_match():
    """
    Test if the input notes match the Nahawand scale at shift 9 (starting on A).
    """
    # The exact input notes from the visualization
    input_midi_notes = [57, 59, 60, 62, 64, 65]
    
    # Generate the Nahawand scale at shift 9 (starting on A)
    nahawand_scale = generate_nahawand_scale(shift=9, starting_midi_note=57)
    
    print(f"Input MIDI notes: {input_midi_notes}")
    print(f"Nahawand scale (first 20): {nahawand_scale[:20]}")
    
    # Check if each input note is in the Nahawand scale
    matching_notes = 0
    for note in input_midi_notes:
        if note in nahawand_scale:
            matching_notes += 1
            print(f"Note {note} is in the Nahawand scale")
        else:
            print(f"Note {note} is NOT in the Nahawand scale")
    
    # Calculate accuracy
    accuracy = matching_notes / len(input_midi_notes) if len(input_midi_notes) > 0 else 0.0
    print(f"Accuracy: {accuracy:.4f} ({matching_notes}/{len(input_midi_notes)})")
    
    # Also check normalized notes (modulo 12)
    input_normalized = [note % 12 for note in input_midi_notes]
    nahawand_normalized = [note % 12 for note in nahawand_scale]
    
    print(f"\nNormalized input notes: {sorted(set(input_normalized))}")
    print(f"Normalized Nahawand notes: {sorted(set(nahawand_normalized))}")
    
    # Check if each normalized input note is in the normalized Nahawand scale
    matching_normalized = 0
    for note in input_normalized:
        if note in nahawand_normalized:
            matching_normalized += 1
            print(f"Normalized note {note} is in the Nahawand scale")
        else:
            print(f"Normalized note {note} is NOT in the Nahawand scale")
    
    # Calculate normalized accuracy
    normalized_accuracy = matching_normalized / len(input_normalized) if len(input_normalized) > 0 else 0.0
    print(f"Normalized accuracy: {normalized_accuracy:.4f} ({matching_normalized}/{len(input_normalized)})")
    
    # Print the note names for reference
    note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    print("\nNote names:")
    for i, name in enumerate(note_names):
        print(f"  {i}: {name}")
    
    # Print the Nahawand scale at shift 9 (starting on A)
    print("\nNahawand scale at shift 9 (starting on A):")
    for note in sorted(set(nahawand_normalized)):
        print(f"  {note}: {note_names[note]}")
    
    # Print the input notes
    print("\nInput notes:")
    for note in sorted(set(input_normalized)):
        print(f"  {note}: {note_names[note]}")

if __name__ == "__main__":
    test_nahawand_match()