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
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Use a Sample", f"{musical_note}Sing/Hum{microphone}", "Upload", "Add to the Library", "Explore Song Library", "How Does it Work?"])

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


    with tab6:
        st.header("How does it work?")

        st.subheader("1. Extracting Vocals")
        st.write("""
        The first step involves extracting the vocal track from the audio file for each audio file added to the library. This is done using the **Demucs** algorithm, which is a state-of-the-art music source separation tool. It isolates the vocal track from the accompaniment, providing a clearer input for the next steps.
        """)

        st.subheader("2. Converting to MIDI")
        st.write("""
        After isolating the vocals, we convert the audio into MIDI format using the **Melodia** algorithm. This process essentially translates the sound into musical notes, capturing the melody of the vocal track. Apparently, this is much harder than converting instrument sounds to melodies.
        """)
        st.write("***Note:*** *You can check out the melody that was extracted from the query and results using the \"Download MIDI\" and check them out with a [MIDI parser](https://signal.vercel.app/edit).*")

        st.subheader("3. Chunking MIDI Files")
        st.write("""
        The MIDI files are then split into chunks of 20 seconds with overlaps. This chunking helps us match segments of the melody more effectively and also enables us to create timestamped links to YouTube, which is a cool feature. Each chunk is processed individually in the subsequent steps.
        """)

        st.subheader("4. Standardizing to the Same Key")
        st.write("""
        To ensure consistency, we normalize the notes by subtracting the median pitch in each chunk. This step standardizes the melody to a common key, making it easier to compare different tracks.
        """)

        st.subheader("5. Vector Representation")
        st.write("""
        We create a histogram of the normalized notes, which serves as a vector representation of the melody. Vector representations are a foundational concept in modern AI, used in everything from Netflix recommendations to language models like ChatGPT. The idea is to map data to a space where similar items are close together, making it easier to identify and compare them.
        
        - **Similarity in Space**: In AI, having similar items close together in a vector space allows for efficient similarity searches and comparisons.
        - **Training Data**: Typically, creating effective vector representations requires training on large amounts of data to capture the underlying meaning or structure.
        - **Note Histogram**: In our case, we leverage the histogram of notes as a kind of shortcut. While it loses much of the detailed information, it is highly effective for prefiltering using cosine similarity.
        - **Bag of Notes**: Similar to a "bag of words" model in text analysis, this histogram focuses on the frequency and occurrence of each note rather than their order.
        """)

        st.subheader("6. Cosine Similarity Prefiltering")
        st.write("""
        Using the histogram representation, we calculate the cosine similarity between the query and reference tracks. This prefiltering step helps us quickly identify the top N candidate matches that are most similar to the query.
        """)

        st.subheader("7. Reranking with Modified DTW Algorithm")
        st.write("""
        The top N results from the prefiltering step are then reranked using a modified **Dynamic Time Warping (DTW)** algorithm. This advanced algorithm accounts for variations in tempo and note duration, providing a more accurate match by considering the sequence and timing of notes.
        - **Stretch Penalty**: A penalty is applied for long stretches of horizontal or vertical steps in the DTW path, which helps to penalize long mismatches.
        """)


        st.write("""
        This comprehensive approach ensures that the most accurate matches are identified, even if the melodies have variations in tempo or pitch.
        """)

               
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

