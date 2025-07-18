"""
Maqam Visualization Module

This module provides visualization tools for maqam detection results, including:
1. Histogram overlap visualization
2. Note distribution visualization
3. Maqam scale visualization
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import List, Dict, Tuple, Optional
import io
import base64
from maqam_core import get_maqam, get_all_maqams
from maqam_analysis import calculate_note_histogram
from maqam_constants import NOTE_NAMES
import streamlit as st

def get_note_name_from_index(index: int, base_index: int = -24) -> str:
    """
    Get the note name from a histogram bin index.
    
    Args:
        index: Bin index in the histogram
        base_index: Starting index of the histogram bins
        
    Returns:
        Note name string
    """
    # Define note names
    note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    quarter_tone_names = {
        1: "¼↑",  # Quarter sharp
        3: "¼↓"   # Quarter flat
    }
    
    # Calculate the actual note value
    note_value = index + base_index
    
    # Get the note within the octave
    note_in_octave = note_value % 24
    
    # Calculate semitone and quarter tone component
    semitone = int(note_in_octave / 2)
    quarter = note_in_octave % 2
    
    # Get base note name
    base_name = note_names[semitone % 12]
    
    # Add quarter tone modifier if needed
    if quarter in quarter_tone_names:
        return f"{base_name}{quarter_tone_names[quarter]}"
    else:
        return base_name

def visualize_absolute_note_distribution(notes: List[float]) -> plt.Figure:
    """
    Visualize the absolute note distribution from the input notes without normalization,
    with a piano-like representation of black and white keys.
    
    Args:
        notes: List of note values
        
    Returns:
        Matplotlib figure
    """
    if len(notes) == 0:
        return None
    
    # Convert quarter tone notes to MIDI notes
    midi_notes = [int(round(note / 2)) for note in notes]
    
    # Find the range of notes
    min_note = min(midi_notes)
    max_note = max(midi_notes)
    
    # Extend the range to show more context (at least 2 octaves)
    range_size = max_note - min_note
    if range_size < 24:  # 2 octaves
        padding = (24 - range_size) // 2
        min_note = max(0, min_note - padding)  # Don't go below 0
        max_note = min_note + 24 + padding
    
    # Create a histogram of the notes
    note_range = range(min_note, max_note + 1)
    hist = np.zeros(len(note_range))
    
    for note in midi_notes:
        if min_note <= note <= max_note:
            hist[note - min_note] += 1
    
    # Normalize the histogram
    if np.sum(hist) > 0:
        hist = hist / np.sum(hist)
    
    # Create figure
    fig, ax = plt.subplots(figsize=(14, 6))
    
    # X-axis labels (note names with octaves)
    x = np.arange(len(hist))
    
    # Generate note names with octaves and determine which are black keys
    note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    labels = []
    is_black_key = []
    
    for midi_note in range(min_note, max_note + 1):
        octave = (midi_note // 12) - 1
        note_idx = midi_note % 12
        note_name = note_names[note_idx]
        labels.append(f"{note_name}{octave}")
        # C#, D#, F#, G#, A# are black keys
        is_black_key.append(note_name.endswith('#'))
    
    # Create colors for bars (white keys are light gray, black keys are dark gray)
    # colors = ['#1a1a1a' if black else '#999999' for black in is_black_key]
    colors = ['#0d0d0d' if black else '#d0d0d0' for black in is_black_key]

    
    # Plot histogram with piano-like coloring
    bars = ax.bar(x, hist, width=0.8, color=colors, alpha=0.8)
    
    # Highlight the bars that have notes in the input
    for i, count in enumerate(hist):
        if count > 0:
            bars[i].set_color('#1f77b4')  # Highlight with blue
            bars[i].set_alpha(0.9)
    
    # Set x-axis labels
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=8)
    
    # Add vertical grid lines to separate octaves
    for i in range(len(hist)):
        if labels[i].endswith('C0') or labels[i].endswith('C1') or labels[i].endswith('C2') or \
           labels[i].endswith('C3') or labels[i].endswith('C4') or labels[i].endswith('C5') or \
           labels[i].endswith('C6') or labels[i].endswith('C7') or labels[i].endswith('C8'):
            ax.axvline(x=i, color='#dddddd', linestyle='-', alpha=0.5)
    
    # Set labels and title
    ax.set_xlabel('Note')
    ax.set_ylabel('Frequency')
    ax.set_title('Absolute Note Distribution (Piano Representation)')
    
    # Add a legend explaining the colors
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#1f77b4', alpha=0.9, label='Notes in melody'),
        Patch(facecolor='#333333', alpha=0.8, label='Black keys'),
        Patch(facecolor='#999999', alpha=0.8, label='White keys')
    ]
    ax.legend(handles=legend_elements, loc='upper right')
    
    plt.tight_layout()
    
    return fig


def visualize_maqam_comparison(input_notes: List[float], maqam_name: str, shift: int = 0, 
                              starting_midi_note: int = 60) -> plt.Figure:
    """
    Visualize the comparison between input notes and maqam scale, starting from the actual
    starting note of the melody and showing 3 octaves of the maqam.
    
    Args:
        input_notes: List of input note values
        maqam_name: Name of the maqam to compare with
        shift: Shift value for the maqam
        starting_midi_note: MIDI note number of the starting note
        
    Returns:
        Matplotlib figure
    """
    maqam = get_maqam(maqam_name)
    if not maqam:
        return None
    
    # Convert quarter tone notes to MIDI notes
    midi_notes = [int(round(note / 2)) for note in input_notes]
    
    # Find the range of notes
    min_note = min(midi_notes)
    max_note = max(midi_notes)
    
    # Calculate the maqam's root note based on the shift
    maqam_root_index = shift % 12
    
    # Find the octave of the starting note
    octave = starting_midi_note // 12
    
    # Calculate the maqam's root note in the same octave as the starting note
    maqam_root_note = maqam_root_index + (octave * 12)
    
    # Adjust the range to center around the maqam's root note
    range_min = maqam_root_note - 12  # One octave below
    range_max = maqam_root_note + 24  # Two octaves above
    
    # Ensure we include all input notes
    range_min = min(range_min, min_note)
    range_max = max(range_max, max_note)
    
    # Create a histogram of the input notes
    note_range = range(range_min, range_max + 1)
    input_hist = np.zeros(len(note_range))
    
    # Count occurrences of each note in the input
    note_counts = {}
    for note in midi_notes:
        if note in note_counts:
            note_counts[note] += 1
        else:
            note_counts[note] = 1
    
    # Fill the histogram
    for note, count in note_counts.items():
        if range_min <= note <= range_max:
            input_hist[note - range_min] = count
    
    # Normalize the histogram
    if np.sum(input_hist) > 0:
        input_hist = input_hist / np.sum(input_hist)
        
    # Print debug info
    print(f"Visualization - Input notes: {sorted(note_counts.keys())}")
    print(f"Visualization - Maqam: {maqam_name}, Shift: {shift}, Starting at: {range_min}")
    
    # Get the maqam scale with the specified shift
    maqam_scale = maqam.get_scale_with_shift(
        shift=shift,
        min_note=range_min,
        max_note=range_max
    )
    
    # Create a histogram for the maqam scale
    maqam_hist = np.zeros_like(input_hist)
    for note in maqam_scale:
        if range_min <= note <= range_max:
            maqam_hist[note - range_min] += 1
    
    # Normalize the maqam histogram
    if np.sum(maqam_hist) > 0:
        maqam_hist = maqam_hist / np.sum(maqam_hist)
    
    # Calculate the maqam's root note based on the shift
    maqam_root_index = (shift % 12)  # The shift directly indicates the root note
    maqam_root_note = NOTE_NAMES[maqam_root_index]
    
    # Create figure
    fig, ax = plt.subplots(figsize=(14, 6))
    
    # X-axis labels (note names with octaves)
    x = np.arange(len(input_hist))
    
    # Generate note names with octaves and determine which are black keys
    labels = []
    is_black_key = []
    
    for midi_note in range(range_min, range_max + 1):
        octave = (midi_note // 12) - 1
        note_idx = midi_note % 12
        note_name = NOTE_NAMES[note_idx]
        labels.append(f"{note_name}{octave}")
        # C#, D#, F#, G#, A# are black keys
        is_black_key.append(note_name.endswith('#'))
    
    # Create colors for bars (white keys are light, black keys are very dark)
    colors = ['#0d0d0d' if black else '#d0d0d0' for black in is_black_key]
    
    # Plot the piano keyboard background
    for i, color in enumerate(colors):
        ax.bar(x[i], 0.05, width=0.8, color=color, alpha=0.3, bottom=-0.05)
    
    # Plot histograms
    width = 0.35
    bars1 = ax.bar(x - width/2, input_hist, width, label='Input Notes', alpha=0.7, color='#1f77b4')
    bars2 = ax.bar(x + width/2, maqam_hist, width, label=f'{maqam.name} Scale', alpha=0.7, color='#ff7f0e')

    # Highlight both the starting note of the input melody and the maqam's root note
    starting_note_mod12 = (int(round(min(input_notes) / 2))) % 12
    maqam_root_mod12 = shift % 12  # The maqam's root note is determined by the shift
    
    for i, midi_note in enumerate(range(range_min, range_max + 1)):
        # Highlight input melody starting note
        if midi_note % 12 == starting_note_mod12 and i < len(input_hist) and input_hist[i] > 0:
            bars1[i].set_color('#0066cc')  # Darker blue
        
        # Highlight maqam root note
        if midi_note % 12 == maqam_root_mod12 and i < len(maqam_hist) and maqam_hist[i] > 0:
            bars2[i].set_height(maqam_hist[i] * 1.3)  # 30% taller
            bars2[i].set_color('#cc5500')  # Darker orange
    
    # Set x-axis labels
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=8)
    
    # Add vertical grid lines to separate octaves
    for i in range(len(labels)):
        if labels[i].endswith('C0') or labels[i].endswith('C1') or labels[i].endswith('C2') or \
           labels[i].endswith('C3') or labels[i].endswith('C4') or labels[i].endswith('C5') or \
           labels[i].endswith('C6') or labels[i].endswith('C7') or labels[i].endswith('C8'):
            ax.axvline(x=i, color='#dddddd', linestyle='-', alpha=0.5)
    
    # Set labels and title
    ax.set_xlabel('Note')
    ax.set_ylabel('Frequency')
    ax.set_title(f'Note Distribution: Input vs {maqam.name} Scale starting on {maqam_root_note}')
    ax.legend()
    
    plt.tight_layout()
    
    return fig

# def visualize_top_maqams(input_notes: List[float], maqam_results: List[Tuple[str, float, int]], 
#                         max_maqams: int = 3) -> List[plt.Figure]:
#     """
#     Visualize the top matching maqams.
    
#     Args:
#         input_notes: Input note sequence
#         maqam_results: List of (maqam_name, confidence, shift) tuples
#         max_maqams: Maximum number of maqams to visualize
        
#     Returns:
#         List of matplotlib figures
#     """
#     # Create visualizations for top maqams
#     figures = []
#     for result in maqam_results[:max_maqams]:
#         # Handle different result formats
#         if len(result) >= 5:
#             maqam_name, confidence, shift, _, starting_midi_note = result
#         elif len(result) >= 4:
#             maqam_name, confidence, shift, _ = result
#             starting_midi_note = int(round(min(input_notes) / 2)) if len(input_notes) > 0 else 0
#         else:
#             maqam_name, confidence, shift = result
#             starting_midi_note = int(round(min(input_notes) / 2)) if len(input_notes) > 0 else 0
            
#         fig = visualize_maqam_comparison(input_notes, maqam_name, shift, starting_midi_note)
#         if fig:
#             figures.append(fig)
    
#     return figures

def fig_to_base64(fig: plt.Figure) -> str:
    """
    Convert a matplotlib figure to base64 string for embedding in HTML.
    
    Args:
        fig: Matplotlib figure
        
    Returns:
        Base64 encoded string
    """
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100)
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return img_str

def create_midi_player_widget(midi_file_path: str) -> None:
    """
    Create an interactive MIDI player widget with note visualization using streamlit_pianoroll.
    
    Args:
        midi_file_path: Path to the MIDI file
    """
    try:
        # Try to import the required libraries
        import streamlit_pianoroll
        from fortepyan import MidiPiece
        import mido
        import tempfile
        
        # First, try to load the MIDI file directly
        try:
            piece = MidiPiece.from_file(midi_file_path)
            
            # Display the piano roll
            st.write("### Piano Roll Playback")
            streamlit_pianoroll.from_fortepyan(piece)
            return
        except Exception as direct_load_error:
            # If direct loading fails, try to normalize the MIDI file
            try:
                # Load the MIDI file using mido
                midi_file = mido.MidiFile(midi_file_path)
                
                # Create a new MIDI file with normalized structure
                # Use the same ticks_per_beat as the original to maintain timing
                normalized_midi = mido.MidiFile(ticks_per_beat=midi_file.ticks_per_beat)
                
                # Add a track for metadata
                meta_track = mido.MidiTrack()
                normalized_midi.tracks.append(meta_track)
                
                # Add tempo information
                meta_track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(120), time=0))
                
                # Add instrument information (Piano)
                meta_track.append(mido.MetaMessage('track_name', name='Melody', time=0))
                meta_track.append(mido.Message('program_change', program=0, time=0))
                
                # Create a track for notes
                note_track = mido.MidiTrack()
                normalized_midi.tracks.append(note_track)
                
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
                
                # Save the normalized MIDI file
                with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as tmp_file:
                    normalized_midi_path = tmp_file.name
                
                normalized_midi.save(normalized_midi_path)
                
                # Try to load the normalized MIDI file
                piece = MidiPiece.from_file(normalized_midi_path)
                
                # Display the piano roll
                st.write("### Piano Roll Playback")
                streamlit_pianoroll.from_fortepyan(piece)
                
                # Clean up the temporary file
                import os
                os.unlink(normalized_midi_path)
                
            except Exception as normalize_error:
                st.warning("Could not visualize MIDI file in piano roll format. Using simplified display instead.")
                
                # Create a simplified visualization
                try:
                    midi_file = mido.MidiFile(midi_file_path)
                    
                    # Extract note information
                    notes = []
                    for track in midi_file.tracks:
                        current_time = 0
                        for msg in track:
                            current_time += msg.time
                            if msg.type == 'note_on' and msg.velocity > 0:
                                notes.append((current_time, msg.note))
                    
                    # Create a simple visualization
                    if notes:
                        import matplotlib.pyplot as plt
                        import numpy as np
                        
                        # Extract times and pitches
                        times = [note[0] for note in notes]
                        pitches = [note[1] for note in notes]
                        
                        # Create the plot
                        fig, ax = plt.subplots(figsize=(10, 4))
                        ax.scatter(times, pitches, alpha=0.7, s=30)
                        ax.set_xlabel('Time (ticks)')
                        ax.set_ylabel('MIDI Note')
                        ax.set_title('MIDI Notes Visualization')
                        
                        # Add piano keyboard on y-axis
                        ax.set_yticks(range(min(pitches)-2, max(pitches)+3))
                        ax.grid(True, axis='y', alpha=0.3)
                        
                        # Highlight black keys with gray background
                        for note in range(21, 109):
                            if note % 12 in [1, 3, 6, 8, 10]:  # Black keys
                                ax.axhspan(note-0.5, note+0.5, color='lightgray', alpha=0.3)
                        
                        st.pyplot(fig)
                    else:
                        st.warning("No notes found in the MIDI file.")
                
                except Exception as simple_viz_error:
                    st.error(f"Error creating simplified MIDI visualization: {simple_viz_error}")
    
    except ImportError:
        st.error("Required libraries not found. Please install streamlit_pianoroll and fortepyan.")
        st.info("You can install them with: pip install streamlit_pianoroll fortepyan")
        
        # Fall back to the download button
        st.info("You can still download the MIDI file using the download button above.")
        
    except Exception as e:
        st.error(f"Error creating MIDI player: {e}")
        st.info("You can still download the MIDI file using the download button above.")


def display_maqam_results_streamlit(input_notes: List[float], maqam_results: List[Tuple[str, float, int, float]],
                                   max_maqams: int = 10, midi_file_path: str = None) -> None:
    """
    Display maqam detection results in Streamlit.
    
    Args:
        input_notes: Input note sequence
        maqam_results: List of (maqam_name, confidence, shift, original_pitch) tuples
        max_maqams: Maximum number of maqams to visualize
        midi_file_path: Path to the MIDI file for playback (optional)
    """
    # Skip the absolute note distribution section as requested
    
    st.subheader("Maqam Detection Results")
    
    # Display top maqams in a table
    st.write("Top matching maqams:")
    
    # Create a table for the results
    table_data = []
    for i, result in enumerate(maqam_results[:max_maqams]):
        # Handle different result formats
        if len(result) == 5:
            maqam_name, confidence, shift, original_pitch, starting_midi_note = result
        elif len(result) == 4:
            maqam_name, confidence, shift, original_pitch = result
            starting_midi_note = int(round(min(input_notes) / 2)) if len(input_notes) > 0 else 0
        else:
            maqam_name, confidence, shift = result
            original_pitch = np.median(input_notes) if len(input_notes) > 0 else 0
            starting_midi_note = int(round(min(input_notes) / 2)) if len(input_notes) > 0 else 0
            
        maqam = get_maqam(maqam_name)
        if not maqam:
            continue
            
        # Get the note names
        note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        
        # Calculate the actual starting note of the melody
        # Get the octave number (C4 = middle C, MIDI note 60)
        octave = (starting_midi_note // 12) - 1
        
        # Get the note name within the octave
        note_index = starting_midi_note % 12
        note_name = note_names[note_index]
        
        # Combine note name and octave for the melody's starting note
        melody_starting_note = f"{note_name}{octave}"
        
        # Calculate the maqam's root note based on the shift
        # The shift directly indicates the root note (0 = C, 1 = C#, ..., 9 = A, etc.)
        maqam_base_note_index = shift % 12
        maqam_base_note = note_names[maqam_base_note_index]
        
        # Create a description of the match
        match_description = f"{maqam.name} starting on {maqam_base_note}"
        
        table_data.append({
            "Rank": i+1,
            "Maqam": maqam.name,
            "Score": f"{confidence:.2f}",
            "Melody Starts On": melody_starting_note,
            "Maqam Pattern": match_description
        })
    
    st.table(table_data)
    
    # Display description of the top maqam
    if maqam_results:
        top_maqam_name = maqam_results[0][0]
        top_maqam = get_maqam(top_maqam_name)
        if top_maqam:
            st.subheader(f"About {top_maqam.name}")
            st.write(top_maqam.description)
            st.write(f"**Common Uses:** {top_maqam.common_uses}")
    
    # Display histogram visualizations
    st.subheader("Note Distribution Comparison")
    
    # Calculate input histogram
    input_hist = calculate_note_histogram(input_notes)
    
    # Create tabs for each maqam visualization
    if len(maqam_results) > 0:
        # Get maqam names for tabs, handling both result formats
        tab_names = []
        for result in maqam_results[:max_maqams]:
            maqam_name = result[0]  # First element is always the maqam name
            maqam = get_maqam(maqam_name)
            if maqam:
                tab_names.append(maqam.name)
        
        tabs = st.tabs(tab_names)
        
        for i, (tab, result) in enumerate(zip(tabs, maqam_results[:max_maqams])):
            # Handle all possible result formats
            if len(result) == 5:
                maqam_name, confidence, shift, _, starting_midi_note = result
            elif len(result) == 4:
                maqam_name, confidence, shift, _ = result
                starting_midi_note = int(round(min(input_notes) / 2)) if len(input_notes) > 0 else 0
            else:
                maqam_name, confidence, shift = result
                starting_midi_note = int(round(min(input_notes) / 2)) if len(input_notes) > 0 else 0
                
            with tab:
                # Use the new visualization function that shows both input notes and maqam scale
                fig = visualize_maqam_comparison(input_notes, maqam_name, shift, starting_midi_note)
                if fig:
                    st.pyplot(fig)
                    
                    # Show the maqam scale
                    maqam = get_maqam(maqam_name)
                    if maqam:
                        st.write(f"**{maqam.name} Scale:**")
                        scale_notes = []
                        for interval in maqam.p_intervals:
                            if interval == 2:
                                scale_notes.append("Whole step")
                            elif interval == 1.5:
                                scale_notes.append("3/4 step")
                            elif interval == 1:
                                scale_notes.append("Half step")
                            elif interval == 0.5:
                                scale_notes.append("Quarter step")
                            else:
                                scale_notes.append(f"{interval} steps")
                        
                        st.write(" → ".join(scale_notes))