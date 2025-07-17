"""
Comprehensive script to analyze all maqams with the exact input notes from the debug output.
"""

import numpy as np
from typing import List, Tuple
from maqam_definitions import get_maqam, get_all_maqams, calculate_maqam_accuracy_score

def analyze_input_with_all_maqams(input_notes: List[float]) -> None:
    """
    Analyze the input notes with all maqams and all shifts.
    
    Args:
        input_notes: List of note values from the debug output
    """
    print(f"Input notes: {input_notes}")
    
    # Convert to quarter tone values (as in the original code)
    input_quarter_tones = input_notes
    
    # Calculate the starting note
    starting_note = int(round(min(input_quarter_tones) / 2)) if len(input_quarter_tones) > 0 else 0
    print(f"Starting MIDI note: {starting_note}")
    
    # Analyze each maqam
    for maqam_name, maqam in [(m.name.lower(), m) for m in get_all_maqams()]:
        print(f"\nAnalyzing maqam: {maqam.name}")
        
        # Try all 12 semitone shifts
        for shift in range(0, 12):
            # Generate the maqam scale
            maqam_scale = generate_maqam_scale(maqam, shift, starting_note)
            
            # Calculate accuracy
            is_nahawand = (maqam_name.lower() == "nahawand")
            accuracy = calculate_maqam_accuracy_score(input_quarter_tones, maqam_scale, use_semitones=True, is_nahawand=is_nahawand)
            
            # Calculate the maqam's root note based on the shift
            note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
            maqam_root_index = (shift % 12)
            maqam_root_note = note_names[maqam_root_index]
            
            print(f"  Shift {shift} (starting on {maqam_root_note}): accuracy = {accuracy:.4f}")

def generate_maqam_scale(maqam, shift: int, starting_note: int) -> List[int]:
    """
    Generate a maqam scale with the specified shift.
    
    Args:
        maqam: The maqam object
        shift: The shift value (0-11)
        starting_note: The MIDI note number of the starting note
        
    Returns:
        List of note values in the maqam scale
    """
    # Get the semitone positions of each note in the maqam
    semitone_positions = []
    current_pos = 0
    
    # Convert quarter tone intervals to semitone positions
    for i, interval in enumerate(maqam.intervals):
        semitone_positions.append(current_pos)  # Keep as quarter tones
        current_pos += interval
    
    # Remove the last position (octave) to avoid duplicates
    semitone_positions = semitone_positions[:-1]
    
    # Generate 5 octaves of the maqam scale centered around the starting note
    maqam_scale = []
    base_octave = (starting_note // 12) - 2  # Start 2 octaves below
    for octave in range(base_octave, base_octave + 5):  # 5 octaves total
        for pos in semitone_positions:
            # Convert to quarter tone system (24 quarter tones per octave)
            note = octave * 24 + pos + (shift * 2)  # Multiply shift by 2 for quarter tones
            maqam_scale.append(note)
    
    return maqam_scale

def main():
    # Use the exact input notes from the debug output
    input_notes = [114, 128, 128, 124, 120, 124, 128, 130, 128, 124]
    
    # Analyze with all maqams
    analyze_input_with_all_maqams(input_notes)

if __name__ == "__main__":
    main()