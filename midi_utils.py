import streamlit as st
from midi2audio import FluidSynth
import tempfile
from pydub import AudioSegment
from consts import CHUNKS_DIR
import os
from audio_processing import extract_midi_chunk, save_midi_chunk

def play_midi(midi_path):
    soundfont = "/usr/share/sounds/sf2/FluidR3_GM.sf2"  # Path to your soundfont file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_wav:
        fs = FluidSynth(sound_font=soundfont)
        fs.midi_to_audio(midi_path, tmp_wav.name)

        # Increase volume using pydub
        audio = AudioSegment.from_wav(tmp_wav.name)
        louder_audio = audio + 20  # Increase volume by 20 dB
        louder_audio.export(tmp_wav.name, format="wav")

        st.audio(tmp_wav.name, format="audio/wav")

def download_button(data, filename, text):
    st.download_button(label=text, data=data, file_name=filename, mime='application/octet-stream')

def display_results(top_matches, query_midi_path, debug=False):
    st.subheader("Top Matches:")

    for i, match in enumerate(top_matches):
        cosine_similarity_score, dtw_score, start_time, shift, path, median_diff_semitones, track = match

        st.markdown(f"**Match {i + 1}:** {track}")
        st.write(
            f"Cosine Similarity Score: {cosine_similarity_score:.2f}, DTW Score: {dtw_score:.2f}, Start time: {start_time:.2f}, Shift: {shift} semitones, Median difference: {median_diff_semitones} semitones")

        # Ensure that the MIDI chunk is created before proceeding
        chunk = extract_midi_chunk(query_midi_path, start_time)
        if chunk:
            chunk_path = os.path.join(CHUNKS_DIR, f"{track}_chunk_{i}.mid")
            save_midi_chunk(chunk, chunk_path)

            # Only attempt to download or play if the chunk file exists
            if os.path.exists(chunk_path):
                st.markdown(midi_download_str, unsafe_allow_html=True)
                # Play the MIDI result
                play_midi(chunk_path)
                midi_download_str = download_button(open(chunk_path, "rb").read(), f"{track}_chunk.mid",
                                                    "Download Result MIDI Chunk")
            else:
                st.write(f"Chunk file {chunk_path} not found.")
        else:
            st.write(f"Failed to extract chunk for {track}.")

        if debug:
            display_path(path)
