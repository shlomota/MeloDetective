import streamlit as st
from midi2audio import FluidSynth
import tempfile
from pydub import AudioSegment
from consts import CHUNKS_DIR, MIDIS_DIR, IMAGES_DIR
import os
import uuid
from audio_processing import extract_midi_chunk, save_midi_chunk
from utils import display_path

def play_midi(midi_path):
    soundfont = "/usr/share/sounds/sf2/FluidR3_GM.sf2"  # Path to your soundfont file
    unique_id = uuid.uuid4()  # Generate a unique identifier for the temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{unique_id}.wav") as tmp_wav:
        fs = FluidSynth(sound_font=soundfont)
        fs.midi_to_audio(midi_path, tmp_wav.name)

        # Increase volume using pydub
        audio = AudioSegment.from_wav(tmp_wav.name)
        louder_audio = audio + 20  # Increase volume by 20 dB
        louder_audio.export(tmp_wav.name, format="wav")

        st.audio(tmp_wav.name, format="audio/wav")

    # Clean up the temporary file
    os.remove(tmp_wav.name)

def download_button(data, filename, text):
    st.download_button(label=text, data=data, file_name=filename, mime='application/octet-stream')

def find_midi_file(track_name):
    midi_path = os.path.join(MIDIS_DIR, f"{track_name}.mid")
    if os.path.exists(midi_path):
        return midi_path
    else:
        st.write(f"MIDI file for {track_name} not found in {MIDIS_DIR}.")
        return None

def display_results(top_matches, query_midi_path, debug=False):
    st.subheader("Top Matches:")

    # Display the query image larger
    query_image_path = os.path.join(IMAGES_DIR, os.path.basename(query_midi_path).replace('.mid', '.png'))
    if os.path.exists(query_image_path):
        st.image(query_image_path, caption="Query MIDI Notes", use_column_width=True)

    for i, match in enumerate(top_matches):
        cosine_similarity_score, dtw_score, start_time, shift, path, median_diff_semitones, track_name = match

        st.markdown(f"**Match {i + 1}:** {track_name}")
        st.write(
            f"Cosine Similarity Score: {cosine_similarity_score:.2f}, DTW Score: {dtw_score:.2f}, Start time: {start_time:.2f}, Shift: {shift} semitones, Median difference: {median_diff_semitones} semitones")

        # Find the MIDI file using track_name
        midi_file_path = find_midi_file(track_name)
        if midi_file_path:
            # Extract a 20-second chunk from the matched MIDI file
            chunk = extract_midi_chunk(midi_file_path, start_time, duration=20)
            if chunk:
                chunk_path = os.path.join(CHUNKS_DIR, f"{track_name}_chunk_{i}.mid")
                save_midi_chunk(chunk, chunk_path)

                # Only attempt to download or play if the chunk file exists
                if os.path.exists(chunk_path):
                    # Layout: Play MIDI on the left, image on the right
                    with st.container():
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            st.write(f"Playing result {i + 1}:")
                            play_midi(chunk_path)
                        with col2:
                            result_image_path = os.path.join(IMAGES_DIR, f"{track_name}.png")
                            if os.path.exists(result_image_path):
                                st.image(result_image_path, caption=f"{track_name} Notes", use_column_width=True)

                    # Uncomment if you want a download button
                    # midi_download_str = download_button(open(chunk_path, "rb").read(), f"{track_name}_chunk.mid", "Download Result MIDI Chunk")
                    # st.markdown(midi_download_str, unsafe_allow_html=True)
                else:
                    st.write(f"Chunk file {chunk_path} not found.")
            else:
                st.write(f"Failed to extract chunk for {track_name}.")
        else:
            st.write(f"Failed to locate MIDI file for {track_name}.")

        if debug:
            display_path(path)
