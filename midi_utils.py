import streamlit as st
from midi2audio import FluidSynth
import tempfile

def play_midi(midi_path):
    soundfont = "/usr/share/sounds/sf2/FluidR3_GM.sf2"  # Path to your soundfont file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_wav:
        FluidSynth(sound_font=soundfont).midi_to_audio(midi_path, tmp_wav.name)
        st.audio(tmp_wav.name, format="audio/wav")

def download_button(data, filename, text):
    st.download_button(label=text, data=data, file_name=filename, mime='application/octet-stream')
