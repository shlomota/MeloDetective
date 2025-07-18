import base64
import json
import uuid
import re
import pickle
import pandas as pd
import streamlit as st
import os
import tempfile

def download_button(object_to_download, download_filename, button_text, pickle_it=False):
    """
    Generates a link to download the given object_to_download.

    Params:
    ------
    object_to_download:  The object to be downloaded.
    download_filename (str): filename and extension of file. e.g. mydata.csv,
    some_txt_output.txt download_link_text (str): Text to display for download
    link.
    button_text (str): Text to display on download button (e.g. 'click here to download file')
    pickle_it (bool): If True, pickle file.

    Returns:
    -------
    (str): the anchor tag to download object_to_download

    Examples:
    --------
    download_link(your_df, 'YOUR_DF.csv', 'Click to download data!')
    download_link(your_str, 'YOUR_STRING.txt', 'Click to download text!')
    """
    if pickle_it:
        try:
            object_to_download = pickle.dumps(object_to_download)
        except pickle.PicklingError as e:
            st.write(e)
            return None

    else:
        if isinstance(object_to_download, bytes):
            pass

        elif isinstance(object_to_download, pd.DataFrame):
            object_to_download = object_to_download.to_csv(index=False)

        # Try JSON encode for everything else
        else:
            object_to_download = json.dumps(object_to_download)

    try:
        # some strings <-> bytes conversions necessary here
        b64 = base64.b64encode(object_to_download.encode()).decode()

    except AttributeError as e:
        b64 = base64.b64encode(object_to_download).decode()

    button_uuid = str(uuid.uuid4()).replace('-', '')
    button_id = re.sub('\d+', '', button_uuid)

    custom_css = f""" 
        <style>
            #{button_id} {{
                background-color: rgb(255, 255, 255);
                color: rgb(38, 39, 48);
                padding: 0.25em 0.38em;
                position: relative;
                text-decoration: none;
                border-radius: 4px;
                border-width: 1px;
                border-style: solid;
                border-color: rgb(230, 234, 241);
                border-image: initial;

            }} 
            #{button_id}:hover {{
                border-color: rgb(246, 51, 102);
                color: rgb(246, 51, 102);
            }}
            #{button_id}:active {{
                box-shadow: none;
                background-color: rgb(246, 51, 102);
                color: white;
                }}
        </style> """

    dl_link = custom_css + f'<a download="{download_filename}" id="{button_id}" href="data:file/txt;base64,{b64}">{button_text}</a><br></br>'

    return dl_link

def download_midi_button(midi_file_path, download_filename="query.mid", button_text="Download MIDI"):
    """
    Creates a download button specifically for MIDI files, ensuring they are properly formatted.
    
    Args:
        midi_file_path: Path to the MIDI file
        download_filename: Name of the file to download
        button_text: Text to display on the button
        
    Returns:
        HTML string for the download button
    """
    try:
        # Ensure the MIDI file is valid
        import mido
        
        try:
            # Try to load the MIDI file to verify it's valid
            midi_file = mido.MidiFile(midi_file_path)
            
            # Create a standardized MIDI file
            normalized_midi = mido.MidiFile(ticks_per_beat=midi_file.ticks_per_beat)
            
            # Add a track for metadata
            meta_track = mido.MidiTrack()
            normalized_midi.tracks.append(meta_track)
            
            # Add tempo information
            meta_track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(120), time=0))
            
            # Add instrument information (Piano)
            meta_track.append(mido.MetaMessage('track_name', name='Melody', time=0))
            meta_track.append(mido.Message('program_change', program=0, time=0))
            
            # Extract all note events
            active_notes = {}
            notes = []
            
            for track in midi_file.tracks:
                current_time = 0
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
            
            # Create a track for notes
            note_track = mido.MidiTrack()
            normalized_midi.tracks.append(note_track)
            
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
            
            # Save to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mid") as tmp_file:
                normalized_midi_path = tmp_file.name
            
            normalized_midi.save(normalized_midi_path)
            
            # Read the normalized MIDI file
            with open(normalized_midi_path, "rb") as f:
                midi_data = f.read()
            
            # Clean up the temporary file
            os.unlink(normalized_midi_path)
            
        except Exception as e:
            # If normalization fails, try to use the original file
            print(f"MIDI normalization failed: {e}")
            with open(midi_file_path, "rb") as f:
                midi_data = f.read()
        
        # Create the download button
        return download_button(midi_data, download_filename, button_text)
        
    except Exception as e:
        print(f"Error creating MIDI download button: {e}")
        return f"<p>Error creating download button: {e}</p>"