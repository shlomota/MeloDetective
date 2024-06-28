import streamlit as st
from streamlit_mic_recorder import mic_recorder
import traceback
import time
import tempfile
import io
import os
import hashlib
from pydub import AudioSegment
from youtube_search import fetch_metadata_and_download, search_youtube
from audio_processing import trim_audio, process_audio, extract_vocals, convert_to_midi, is_in_library
from utils import setup_logger, display_results, process_and_add_to_library
from download_utils import download_button
from consts import SAMPLE_QUERIES_DIR, LIBRARY_DIR, MIDIS_DIR, METADATA_DIR, LOG_DIR
import consts

# Set page configuration to hide the sidebar by default
st.set_page_config(
    initial_sidebar_state="collapsed",  # Sidebar is collapsed by default
    page_title="Carlebot",
)

st.sidebar.title("Settings")
debug_option = st.sidebar.checkbox("Debug Mode")

# Update the DEBUG variable in consts.py
consts.DEBUG = debug_option


# Ensure all required directories exist
required_dirs = [LIBRARY_DIR, MIDIS_DIR, METADATA_DIR, LOG_DIR]
for dir_path in required_dirs:
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

def search_songs(query, songs):
    return [song for song in songs if query.lower() in song.lower()]

# Assuming songs are the filenames in the library directory
library_songs = [os.path.splitext(f)[0] for f in os.listdir(MIDIS_DIR) if f.endswith('.mid')]

def get_sorted_files_by_mod_time(directory):
    # Get the list of files and their modification times
    files = [(file, os.path.getmtime(os.path.join(directory, file))) for file in os.listdir(directory)]
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

def main():
    st.title("CarleBot: A Carlebach Tune Detector")

    # Create tabs for different options
    musical_note = "\U0001F3B5"
    microphone = "\U0001F3A4"
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Use a Sample Query", f"{musical_note}Sing/Hum{microphone}", "Upload Recording", "Add YouTube Link to Library", "Is My Song in the Database?"])

    with tab1:
        st.write("Select a sample query:")
        sample_queries, sample_queries_display = load_sample_queries()

        selected_query = st.selectbox("Select a sample query", sample_queries_display)

        # Only process if a query is selected
        if selected_query != "Select your query":
            query_path = os.path.join(SAMPLE_QUERIES_DIR, sample_queries[sample_queries_display.index(selected_query) - 1])

            st.write(f"Processing sample query: {selected_query}")
            try:
                audio = AudioSegment.from_file(query_path)
                audio = trim_audio(audio)  # Trim to 20 seconds
                
                # Convert the audio to a format Streamlit can play
                buffer = io.BytesIO()
                audio.export(buffer, format="wav")
                st.audio(buffer.getvalue(), format="audio/wav")
                
                # Process the audio
                top_matches, query_midi_path = process_audio(query_path)
                if top_matches:
                    display_results(top_matches, query_midi_path, search_fallback=True)
            except Exception as e:

                print(traceback.format_exc())
                print(e)
                st.error(f"Error processing sample query: {e}")

    with tab2:
        st.write("Record 20 seconds of audio directly:")
        st.markdown(
            """
            <style>
            .small-font {
                font-size:14px;
            }
            </style>
            """, 
            unsafe_allow_html=True
        )
        st.markdown("<span class='small-font'>***Note:*** *could take a minute to process, on mobile devices you may need to try start and stop twice*</span>", unsafe_allow_html=True)

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
            if top_matches:
                display_results(top_matches, query_midi_path, search_fallback=True)

    with tab3:
        st.write("Upload your audio recording (first 20 seconds will be used)")
        audio_file = st.file_uploader("Choose an audio file", type=['wav', 'mp3', 'ogg'])

        if audio_file is not None:
            start_time = time.time()
            st.write("Uploading and processing the file...")
            
            # Save the uploaded file to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                tmp_file.write(audio_file.getvalue())
                tmp_file_path = tmp_file.name

            st.write(f"Uploaded file in {time.time() - start_time:.2f} seconds.")

            # Now load the audio from the temporary file
            try:
                start_time = time.time()
                audio = AudioSegment.from_file(tmp_file_path)
                audio = trim_audio(audio)  # Trim to 20 seconds
                
                # Convert the audio to a format Streamlit can play
                buffer = io.BytesIO()
                audio.export(buffer, format="wav")
                st.audio(buffer.getvalue(), format="audio/wav")
                
                st.write(f"Processed audio in {time.time() - start_time:.2f} seconds.")

                # Process the audio
                start_time = time.time()
                top_matches, query_midi_path = process_audio(tmp_file_path)
                if top_matches:
                    display_results(top_matches, query_midi_path, search_fallback=True)
                st.write(f"Completed audio processing in {time.time() - start_time:.2f} seconds.")
            except Exception as e:
                print(traceback.format_exc())
                st.error(f"Error processing audio file: {e}")
            finally:
                # Clean up the temporary file
                os.unlink(tmp_file_path)

    with tab4:
        st.write("Add a YouTube link (song or playlist) to the library:")
        youtube_url = st.text_input("YouTube URL")
        if st.button("Add to Library"):
            if youtube_url:
                process_and_add_to_library(youtube_url)
            else:
                st.error("Please enter a valid YouTube URL")

    with tab5:
        st.write("Search for songs in the database:")
        query = st.text_input("Enter song title")
        if query:
            results = search_songs(query, library_songs)
            for result in results[:10]:
                st.write(result)
                
    # Add footer with hyperlink
    st.markdown(
        """
        <div style='text-align: center; padding-top: 20px;'>
            Made by <a href="https://www.linkedin.com/in/shlomo-tannor-aa967a1a8/" target="_blank">Shlomo Tannor</a> |
            <a href="https://github.com/shlomota/MeloDetective" target="_blank">GitHub</a>
        </div>
        """,
        unsafe_allow_html=True
    )
   
if __name__ == "__main__":
    main()

