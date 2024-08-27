import streamlit as st
from streamlit_mic_recorder import mic_recorder
import traceback
import time
import tempfile
import io
import os
from pydub import AudioSegment
from audio_processing import trim_audio, process_audio, extract_vocals, convert_to_midi
from utils import display_results, setup_logger
from consts import SAMPLE_QUERIES_DIR, LIBRARY_DIR, MIDIS_DIR, LOG_DIR
import consts
from midi2audio import FluidSynth
from music21 import converter, midi, instrument, note, chord, stream

# Set page configuration
st.set_page_config(
    initial_sidebar_state="collapsed",  # Sidebar is collapsed by default
    page_title="Niggun Detector",
)

# Ensure all required directories exist
required_dirs = [LIBRARY_DIR, MIDIS_DIR, LOG_DIR]
for dir_path in required_dirs:
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

# Side pane for selecting debug mode
st.sidebar.title("Settings")
debug_option = st.sidebar.checkbox("Debug Mode")
consts.DEBUG = debug_option


def get_sorted_files_by_mod_time(directory):
    # Get the list of files and their modification times
    files = [(file, os.path.getmtime(os.path.join(directory, file))) for file in os.listdir(directory) if
             file.endswith(('.mid', '.midi'))]
    # Sort files by modification time (latest to earliest)
    sorted_files = sorted(files, key=lambda x: x[1], reverse=True)
    # Extract just the filenames
    sorted_filenames = [file[0] for file in sorted_files]
    return sorted_filenames


def remove_file_extension(filename):
    return os.path.splitext(filename)[0].replace("--", "/")


def load_sample_queries():
    sample_queries = get_sorted_files_by_mod_time(SAMPLE_QUERIES_DIR)
    sample_queries_display = ["Select your query"] + [remove_file_extension(file) for file in sample_queries]
    return sample_queries, sample_queries_display


def play_midi(midi_path):
    # Convert MIDI to audio for playback
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_wav:
        FluidSynth().midi_to_audio(midi_path, tmp_wav.name)
        st.audio(tmp_wav.name, format="audio/wav")

    # Visualize MIDI notes
    visualize_midi(midi_path)


def visualize_midi(midi_path):
    # Load the MIDI file
    midi_stream = converter.parse(midi_path)

    # Create a stream with the notes and chords
    notes_to_parse = midi_stream.flat.notes
    notes = []
    for element in notes_to_parse:
        if isinstance(element, note.Note):
            notes.append(str(element.pitch))
        elif isinstance(element, chord.Chord):
            notes.append('.'.join(str(n) for n in element.normalOrder))

    # Display the notes/chords as text for visualization
    st.write("### MIDI Visualization")
    st.write(notes)


def main():
    st.title("Niggun Detector")

    # Create tabs for different options
    musical_note = "\U0001F3B5"
    microphone = "\U0001F3A4"
    tab1, tab2, tab3 = st.tabs(["Upload MIDI", f"{musical_note}Sing/Hum{microphone}", "Use a Sample"])

    with tab1:
        st.write("Upload your MIDI file (first 20 seconds will be used)")
        midi_file = st.file_uploader("Choose a MIDI file", type=['mid', 'midi'])

        if midi_file is not None:
            start_time = time.time()
            st.write("Uploading and processing the file...")

            # Save the uploaded file to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mid") as tmp_file:
                tmp_file.write(midi_file.getvalue())
                tmp_file_path = tmp_file.name

            st.write(f"Uploaded file in {time.time() - start_time:.2f} seconds.")

            # Process the MIDI file and display results
            try:
                start_time = time.time()

                st.write(f"Processing MIDI file: {midi_file.name}")

                # Process the MIDI file
                top_matches, query_midi_path = process_audio(tmp_file_path)

                # Play and download the query MIDI
                st.write("Query MIDI:")
                play_midi(query_midi_path)
                download_str = download_button(open(query_midi_path, "rb").read(), "query.mid", "Download Query MIDI")
                st.markdown(download_str, unsafe_allow_html=True)

                if top_matches:
                    display_results(top_matches, query_midi_path)
                st.write(f"Completed processing in {time.time() - start_time:.2f} seconds.")
            except Exception as e:
                print(traceback.format_exc())
                st.error(f"Error processing MIDI file: {e}")
            finally:
                # Clean up the temporary file
                os.unlink(tmp_file_path)

    with tab2:
        st.write("Record 20 seconds of audio directly:")
        # Record audio using mic_recorder
        audio = mic_recorder(
            start_prompt="Start Recording",
            stop_prompt="Stop Recording",
            just_once=True,
            format="webm",
            key='recorder'
        )

        # If audio data is available, save it and play it back
        if audio:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp_file:
                tmp_file.write(audio['bytes'])
                tmp_file_path = tmp_file.name

            # Convert webm to wav using pydub
            audio_segment = AudioSegment.from_file(tmp_file_path, format="webm")
            wav_tmp_file_path = tmp_file_path.replace(".webm", ".wav")
            audio_segment.export(wav_tmp_file_path, format="wav")

            st.audio(wav_tmp_file_path, format="audio/wav")

            # Process the audio file and display results
            top_matches, query_midi_path = process_audio(wav_tmp_file_path)

            # Play and download the query MIDI
            st.write("Query MIDI:")
            play_midi(query_midi_path)
            download_str = download_button(open(query_midi_path, "rb").read(), "query.mid", "Download Query MIDI")
            st.markdown(download_str, unsafe_allow_html=True)

            if top_matches:
                display_results(top_matches, query_midi_path)

    with tab3:
        st.write("Select a sample query:")
        sample_queries, sample_queries_display = load_sample_queries()

        selected_query = st.selectbox("Select a sample query", sample_queries_display)

        # Only process if a query is selected
        if selected_query != "Select your query":
            query_path = os.path.join(SAMPLE_QUERIES_DIR,
                                      sample_queries[sample_queries_display.index(selected_query) - 1])

            st.write(f"Processing sample query: {selected_query}")
            try:
                # Process the sample MIDI file
                top_matches, query_midi_path = process_audio(query_path)

                # Play and download the query MIDI
                st.write("Query MIDI:")
                play_midi(query_midi_path)
                download_str = download_button(open(query_midi_path, "rb").read(), "query.mid", "Download Query MIDI")
                st.markdown(download_str, unsafe_allow_html=True)

                if top_matches:
                    display_results(top_matches, query_midi_path)
            except Exception as e:
                print(traceback.format_exc())
                st.error(f"Error processing sample query: {e}")

    # Add footer with hyperlink
    st.markdown(
        """
        <div style='text-align: center; padding-top: 20px;'>
Made by <a href="https://www.linkedin.com/in/shlomo-tannor-aa967a1a8/" target="_blank">Shlomo Tannor</a> |
<a href="https://medium.com/@stannor/shazam-for-melodies-how-i-built-melodetective-with-vector-search-and-dtw-7185f54dcb56" target="_blank">Read more on Medium</a> |
<a href="https://github.com/shlomota/MeloDetective" target="_blank">GitHub</a>
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
