"""
Final script to analyze Nahawand maqam detection with the exact input notes from the debug output.
"""

import numpy as np
from typing import List, Tuple
from maqam_definitions import get_maqam, calculate_maqam_accuracy_score

def generate_nahawand_scale(shift: int = 9, starting_note: int = 57) -> List[int]:
    """
    Generate a Nahawand scale with the specified shift.
    
    Args:
        shift: The shift value (0-11)
        starting_note: The MIDI note number of the starting note
        
    Returns:
        List of MIDI note numbers in the Nahawand scale
    """
    # The correct semitone positions for Nahawand (natural minor scale)
    semitone_positions = [0, 2, 3, 5, 7, 8, 10]
    
    # Generate 5 octaves of the maqam scale centered around the starting note
    maqam_scale = []
    base_octave = (starting_note // 12) - 2  # Start 2 octaves below
    for octave in range(base_octave, base_octave + 5):  # 5 octaves total
        for pos in semitone_positions:
            note = octave * 12 + pos + shift
            maqam_scale.append(note)
    
    return sorted(maqam_scale)

def analyze_nahawand_detection(input_notes: List[float]) -> None:
    """
    Analyze Nahawand maqam detection with the input notes.
    
    Args:
        input_notes: List of note values from the debug output
    """
    print(f"Input notes: {input_notes}")
    
    # Convert to quarter tone values (as in the original code)
    input_quarter_tones = input_notes
    
    # Calculate the starting note
    starting_note = int(round(min(input_quarter_tones) / 2)) if len(input_quarter_tones) > 0 else 0
    print(f"Starting MIDI note: {starting_note}")
    
    # Try all 12 semitone shifts for Nahawand
    print("\nTesting all shifts for Nahawand:")
    for shift in range(0, 12):
        # Generate the Nahawand scale with this shift
        nahawand_scale = generate_nahawand_scale(shift, starting_note)
        
        # Calculate accuracy
        accuracy = calculate_maqam_accuracy_score(input_quarter_tones, nahawand_scale, use_semitones=True, is_nahawand=True)
        
        # Calculate the maqam's root note based on the shift
        note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        maqam_root_index = (shift % 12)
        maqam_root_note = note_names[maqam_root_index]
        
        print(f"Shift {shift} (starting on {maqam_root_note}): accuracy = {accuracy:.4f}")
        
        # For shift 9 (A), print more detailed information
        if shift == 9:
            print("\nDetailed analysis for Nahawand at shift 9 (A):")
            
            # Convert to MIDI note numbers
            input_midi_notes = [int(round(note / 2)) for note in input_quarter_tones]
            
            # Get normalized notes (modulo 12)
            input_normalized = sorted(set(note % 12 for note in input_midi_notes))
            nahawand_normalized = sorted(set(note % 12 for note in nahawand_scale))
            
            print(f"Input normalized notes: {input_normalized}")
            print(f"Nahawand normalized notes: {nahawand_normalized}")
            
            # Map to note names
            note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
            
            print("\nInput notes with names:")
            for note in input_normalized:
                print(f"  {note}: {note_names[note]}")
                
            print("\nNahawand notes with names:")
            for note in nahawand_normalized:
                print(f"  {note}: {note_names[note]}")
            
            # Find notes that are in input but not in Nahawand
            missing_notes = set(input_normalized) - set(nahawand_normalized)
            if missing_notes:
                print(f"\nNotes in input but not in Nahawand: {sorted(missing_notes)}")
                for note in sorted(missing_notes):
                    print(f"  {note}: {note_names[note]}")
            else:
                print("\nAll input notes are in the Nahawand scale!")

def main():
    # Use the exact input notes from the debug output
    input_notes = [114, 128, 128, 124, 120, 124, 128, 130, 128, 124]
    
    # Analyze Nahawand detection
    analyze_nahawand_detection(input_notes)

if __name__ == "__main__":
    main()