import streamlit as st
from midi2audio import FluidSynth
import tempfile
from pydub import AudioSegment
from consts import CHUNKS_DIR
import os


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

        midi_path = f"{query_midi_path}_chunk_{i}.mid"
        chunk_path = os.path.join(CHUNKS_DIR, midi_path)
        midi_download_str = download_button(open(chunk_path, "rb").read(), f"{track}_chunk.mid",
                                            "Download Result MIDI Chunk")
        st.markdown(midi_download_str, unsafe_allow_html=True)

        # Play the MIDI result
        st.write(f"Playing result {i + 1}:")
        play_midi(chunk_path)

        if debug:
            display_path(path)
