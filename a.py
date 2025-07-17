import streamlit as st
import streamlit_pianoroll
from fortepyan import MidiPiece
import tempfile

st.title("🎹 Piano Roll MIDI Player")

uploaded_file = st.file_uploader("Upload a MIDI file", type=["mid", "midi"])
if uploaded_file:
    # Save uploaded file to a temporary location
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mid") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    # Now use the path with fortepyan
    piece = MidiPiece.from_file(tmp_path)
    st.write("### Piano Roll Playback")
    streamlit_pianoroll.from_fortepyan(piece)

