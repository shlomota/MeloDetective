import streamlit as st
import traceback
import time
import tempfile
import io
import os
import hashlib
from pydub import AudioSegment
from youtube_search import fetch_metadata_and_download, search_youtube
from audio_processing import trim_audio, process_audio, process_midi_file, extract_vocals, convert_to_midi, is_in_library
from utils import setup_logger, display_results, process_and_add_to_library
from download_utils import download_button
from consts import SAMPLE_QUERIES_DIR, LIBRARY_DIR, MIDIS_DIR, METADATA_DIR, LOG_DIR
import consts
import subprocess

# Try to import streamlit_mic_recorder, but provide a fallback if not available
try:
    from streamlit_mic_recorder import mic_recorder
    MIC_RECORDER_AVAILABLE = True
except ImportError:
    MIC_RECORDER_AVAILABLE = False
    st.warning("streamlit-mic-recorder is not installed. Microphone recording will not be available. Install it with: pip install streamlit-mic-recorder")

# Set page configuration to hide the sidebar by default
st.set_page_config(
    initial_sidebar_state="collapsed",  # Sidebar is collapsed by default
    page_title="Maqam Finder",
)

st.sidebar.title("Settings")
debug_option = st.sidebar.checkbox("Debug Mode")

# Update the DEBUG variable in consts.py
consts.DEBUG = debug_option


# Note: Directory creation is now handled in consts.py

def search_songs(query, songs):
    return [song for song in songs if query.lower() in song.lower()]

# Assuming songs are the filenames in the library directory
try:
    library_songs = [os.path.splitext(f)[0] for f in os.listdir(MIDIS_DIR) if f.endswith('.mid')]
except (FileNotFoundError, PermissionError):
    library_songs = []

def get_sorted_files_by_mod_time(directory):
    # Check if directory exists
    if not os.path.exists(directory):
        return []
    
    # Get the list of files and their modification times
    try:
        files = [(file, os.path.getmtime(os.path.join(directory, file))) for file in os.listdir(directory)]
        # Sort files by modification time (latest to earliest)
        sorted_files = sorted(files, key=lambda x: x[1], reverse=True)
        # Extract just the filenames
        sorted_filenames = [file[0] for file in sorted_files]
        return sorted_filenames
    except (FileNotFoundError, PermissionError):
        return []

def remove_file_extension(filename):
    return os.path.splitext(filename)[0].replace("--", "/")

def ensure_sample_queries_exist():
    """Ensure that at least one sample query exists in the sample queries directory."""
    if not os.path.exists(SAMPLE_QUERIES_DIR):
        os.makedirs(SAMPLE_QUERIES_DIR, exist_ok=True)
    
    # Check if there are any files in the directory
    if not os.listdir(SAMPLE_QUERIES_DIR):
        # Create a simple README file as a placeholder
        readme_path = os.path.join(SAMPLE_QUERIES_DIR, "README.txt")
        with open(readme_path, "w") as f:
            f.write("This directory is for sample audio queries.\n")
            f.write("Add .wav, .mp3, or .ogg files here to use them as samples.\n")

def load_sample_queries():
    # Ensure sample queries directory exists
    ensure_sample_queries_exist()
    
    # Get files from the directory
    if os.path.exists(SAMPLE_QUERIES_DIR) and os.listdir(SAMPLE_QUERIES_DIR):
        sample_queries = [f for f in get_sorted_files_by_mod_time(SAMPLE_QUERIES_DIR) 
                         if f.endswith(('.wav', '.mp3', '.ogg'))]
        if sample_queries:
            sample_queries_display = ["Select your query"] + [remove_file_extension(file) for file in sample_queries]
            return sample_queries, sample_queries_display
    
    # Return empty list if no audio files found
    return [], ["No sample queries available"]

def main():
    st.title("Maqam Finder")

    # Create tabs for different options
    musical_note = "\U0001F3B5"
    microphone = "\U0001F3A4"
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Use a Sample", f"{musical_note}Sing/Hum{microphone}", "Upload Audio", "Upload MIDI", "How Does it Work?"])

    with tab1:
        st.write("Select a sample query:")
        sample_queries, sample_queries_display = load_sample_queries()

        selected_query = st.selectbox("Select a sample query", sample_queries_display)

        # Only process if a query is selected and sample queries exist
        if selected_query != "Select your query" and selected_query != "No sample queries available" and sample_queries:
            try:
                query_path = os.path.join(SAMPLE_QUERIES_DIR, sample_queries[sample_queries_display.index(selected_query) - 1])
                st.write(f"Processing sample query: {selected_query}")
                
                audio = AudioSegment.from_file(query_path)
                audio = trim_audio(audio)  # Trim to 20 seconds
                
                # Convert the audio to a format Streamlit can play
                buffer = io.BytesIO()
                audio.export(buffer, format="wav")
                st.audio(buffer.getvalue(), format="audio/wav")
                
                # Process the audio for maqam detection
                process_audio(query_path)
            except Exception as e:
                print(traceback.format_exc())
                print(e)
                st.error(f"Error processing sample query: {e}")
        elif selected_query == "No sample queries available":
            st.info("No sample audio files found. Please upload an audio file or record using the microphone.")

    with tab2:
        st.write("Record 20 seconds of audio directly:")
        
        if MIC_RECORDER_AVAILABLE:
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

                # Convert webm to wav using ffmpeg
                try:
                    subprocess.run(["ffmpeg", "-i", tmp_file_path, tmp_file_path.replace('.webm', '.wav')], check=True)
                    audio_segment = AudioSegment.from_file(tmp_file_path.replace('.webm', '.wav'), format="wav")

                    wav_tmp_file_path = tmp_file_path.replace(".webm", ".wav")
                    audio_segment.export(wav_tmp_file_path, format="wav")

                    st.audio(wav_tmp_file_path, format="audio/wav")

                    # Process the audio file for maqam detection
                    process_audio(wav_tmp_file_path)
                except Exception as e:
                    st.error(f"Error processing audio: {e}")
                    st.info("Make sure you have ffmpeg installed. You can install it with: brew install ffmpeg (macOS) or apt-get install ffmpeg (Linux)")
        else:
            st.warning("Microphone recording is not available. Please install the streamlit-mic-recorder package with: pip install streamlit-mic-recorder")
            st.info("Alternatively, you can use the 'Upload' tab to upload an audio file for maqam detection.")

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

                # Process the audio for maqam detection
                start_time = time.time()
                process_audio(tmp_file_path)
                st.write(f"Completed audio processing in {time.time() - start_time:.2f} seconds.")
            except Exception as e:
                print(traceback.format_exc())
                st.error(f"Error processing audio file: {e}")
            finally:
                # Clean up the temporary file
                os.unlink(tmp_file_path)

    with tab4:
        st.write("Upload your MIDI file for direct maqam detection")
        midi_file = st.file_uploader("Choose a MIDI file", type=['mid', 'midi'])

        if midi_file is not None:
            start_time = time.time()
            st.write("Uploading and processing the MIDI file...")
            
            # Save the uploaded file to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mid") as tmp_file:
                tmp_file.write(midi_file.getvalue())
                tmp_file_path = tmp_file.name

            st.write(f"Uploaded MIDI file in {time.time() - start_time:.2f} seconds.")

            # Process the MIDI file for maqam detection
            try:
                start_time = time.time()
                process_midi_file(tmp_file_path)
                st.write(f"Completed MIDI processing in {time.time() - start_time:.2f} seconds.")
            except Exception as e:
                print(traceback.format_exc())
                st.error(f"Error processing MIDI file: {e}")
            finally:
                # Clean up the temporary file
                os.unlink(tmp_file_path)

    with tab5:
        st.header("How does it work?")

        st.subheader("1. Enhanced Frequency Analysis")
        st.write("""
        The first step involves analyzing the audio input to extract frequency information with high precision. We use advanced signal processing techniques to detect quarter tones, which are essential for accurately identifying Middle Eastern musical modes (maqams).
        """)

        st.subheader("2. Note Extraction with Quarter Tone Support")
        st.write("""
        The extracted frequencies are converted into a sequence of notes using a specialized numerical system that can represent quarter tones. In this system:
        - Whole step = 4 units
        - Half step = 2 units
        - Quarter step = 1 unit
        
        This allows us to precisely capture the microtonal intervals that are characteristic of maqams.
        """)
        st.write("***Note:*** *You can download the MIDI representation of your input using the \"Download MIDI\" button. While standard MIDI doesn't directly support quarter tones, we use pitch bend to approximate them.*")

        st.subheader("3. Note Normalization")
        st.write("""
        To ensure that the maqam detection works regardless of the absolute pitch you start on, we normalize the note sequence by subtracting the median pitch. This makes the detection pitch-independent, so it works for different vocal ranges and instruments.
        """)

        st.subheader("4. Histogram-Based Representation")
        st.write("""
        We create a histogram of the normalized notes, which serves as a vector representation of the melodic pattern. This approach focuses on the frequency distribution of notes rather than their exact sequence, making it robust to variations in tempo and ornamentation.
        
        - **Note Distribution**: The histogram shows which notes are used most frequently in the melody.
        - **Maqam Fingerprint**: Each maqam has a characteristic note distribution pattern.
        - **Quarter Tone Resolution**: Our histograms have twice the resolution of standard Western music analysis, allowing us to capture the quarter tones.
        """)

        st.subheader("5. Maqam Matching")
        st.write("""
        We compare the histogram of the input melody with the characteristic histograms of different maqams using cosine similarity. This measures how similar the note distributions are, regardless of the absolute starting pitch.
        
        For each maqam, we try different transpositions to find the best match. The system then ranks the maqams by their similarity scores and presents the most likely matches.
        """)

        st.subheader("6. Maqam Library")
        st.write("""
        Our system includes a comprehensive library of Middle Eastern maqams, including:
        
        - **Ajam**: Closely resembles the Western major scale without quarter tones, making it accessible to musicians trained in Western music.
        - **Rast**: Similar to the Western major scale but with a neutral third (between major and minor).
        - **Nahawand**: Similar to the Western minor scale with a distinctive melancholic quality.
        - **Hijaz**: Features an augmented second between the second and third degrees, giving it a distinctive Middle Eastern sound.
        - **Kurd**: Similar to the Western Phrygian mode with a flattened second degree.
        - **Bayati**: Features a neutral second degree (between major and minor), one of the most common maqams in Arabic music.
        - **Saba**: Features a diminished fourth, giving it a very distinctive sound.
        - **Siga**: Features neutral seconds and thirds, giving it a distinctive Middle Eastern sound.
        """)

        st.write("""
        This approach allows us to accurately identify maqams from singing or humming, even with variations in pitch, tempo, and ornamentation that are common in Middle Eastern music performance.
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

