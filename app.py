import os
import streamlit as st
import logging
from utils import display_results
from audio_processing import convert_to_midi, extract_midi_chunk, save_midi_chunk, extract_vocals
from consts import SAMPLE_QUERIES_DIR, LIBRARY_DIR, MIDIS_DIR, LOG_DIR, CHUNKS_DIR

# Set up logging
log_file = os.path.join(LOG_DIR, 'app.log')
logging.basicConfig(filename=log_file, level=logging.INFO)

# Streamlit app layout
st.title("MIDI and Singing/Humming Query by Humming/Singing")

st.sidebar.header("Upload MIDI or WAV File")
file_type = st.sidebar.radio("Choose the type of file to upload:", ("MIDI", "WAV"))

uploaded_file = st.sidebar.file_uploader(f"Choose a {file_type} file", type=["mid", "midi"] if file_type == "MIDI" else ["wav"])

if uploaded_file is not None:
    st.sidebar.write(f"Uploaded {file_type} file: {uploaded_file.name}")

    if file_type == "MIDI":
        # Save uploaded MIDI file
        midi_path = os.path.join(SAMPLE_QUERIES_DIR, uploaded_file.name)
        with open(midi_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.sidebar.write(f"MIDI file saved to: {midi_path}")

        # Process the uploaded MIDI file (e.g., extract chunks, compare with library)
        st.write(f"Processing uploaded MIDI file: {uploaded_file.name}")

        # Example: Extract MIDI chunk and save it
        start_time = 0  # Placeholder, you may extract the start time dynamically
        chunk = extract_midi_chunk(midi_path, start_time)
        if chunk:
            chunk_path = os.path.join(CHUNKS_DIR, f"{uploaded_file.name}_chunk.mid")
            save_midi_chunk(chunk, chunk_path)
            st.write(f"MIDI chunk extracted and saved to: {chunk_path}")
        else:
            st.write("No chunk extracted from the uploaded MIDI file.")

    elif file_type == "WAV":
        # Save uploaded WAV file
        wav_path = os.path.join(SAMPLE_QUERIES_DIR, uploaded_file.name)
        with open(wav_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.sidebar.write(f"WAV file saved to: {wav_path}")

        # Process the uploaded WAV file: Extract vocals and convert to MIDI
        st.write(f"Processing uploaded WAV file: {uploaded_file.name}")
        vocals_path = os.path.join(LIBRARY_DIR, f"{uploaded_file.name}_vocals.wav")
        extract_vocals(wav_path, vocals_path)

        midi_path = os.path.join(MIDIS_DIR, f"{uploaded_file.name}.mid")
        convert_to_midi(vocals_path, midi_path)
        st.write(f"Converted WAV to MIDI and saved to: {midi_path}")

        # Example: Extract MIDI chunk and save it
        start_time = 0  # Placeholder, you may extract the start time dynamically
        chunk = extract_midi_chunk(midi_path, start_time)
        if chunk:
            chunk_path = os.path.join(CHUNKS_DIR, f"{uploaded_file.name}_chunk.mid")
            save_midi_chunk(chunk, chunk_path)
            st.write(f"MIDI chunk extracted and saved to: {chunk_path}")
        else:
            st.write("No chunk extracted from the converted MIDI file.")

    # Assuming `display_results` will now display chunks directly
    # You need to define top_matches with your matching logic
    top_matches = [
        # This is an example; replace it with your actual matching logic
        (0.95, 0.87, 0, 0, None, 0.0, uploaded_file.name)
    ]
    display_results(top_matches, midi_path)

else:
    st.write(f"Please upload a {file_type} file to begin processing.")

# Optional: Additional UI elements for user interaction
