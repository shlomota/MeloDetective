import streamlit as st
from utils import setup_logger
from midi_utils import play_midi, download_button, display_results, find_midi_file
from file_utils import load_sample_queries, get_sorted_files_by_mod_time
from audio_processing import process_audio
from match_midi_agnostic import best_matches, midi_to_pitches_and_times, split_midi
import tempfile
import os
import traceback
import consts
import time
import logging
from consts import IMAGES_DIR, LIBRARY_DIR, SAMPLE_QUERIES_DIR


# Set page configuration
st.set_page_config(
    initial_sidebar_state="collapsed",  # Sidebar is collapsed by default
    page_title="Niggun Detector",
)

# Ensure all required directories exist
required_dirs = [LIBRARY_DIR, consts.MIDIS_DIR, consts.LOG_DIR]
for dir_path in required_dirs:
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

# Side pane for selecting debug mode
st.sidebar.title("Settings")
debug_option = st.sidebar.checkbox("Debug Mode")
consts.DEBUG = debug_option


def main():
    st.title("Niggun Detector")

    # Create tabs for different options
    tab1, tab2 = st.tabs(["Upload MIDI", "Use a Sample"])

    midi_file = None
    query_midi_path = None

    with tab1:
        st.write("Upload your MIDI file (first 20 seconds will be used)")
        midi_file = st.file_uploader("Choose a MIDI file", type=['mid', 'midi'])

        if midi_file is not None:
            start_time = time.time()
            # Save the uploaded file to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mid") as tmp_file:
                tmp_file.write(midi_file.getvalue())
                tmp_file_path = tmp_file.name

            # Process the MIDI file and display results
            try:
                start_time = time.time()

                # Process the MIDI file
                top_matches, query_midi_path = process_audio(tmp_file_path)

                # Play and download the query MIDI
                st.write("Query MIDI:")
                with st.container():
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        play_midi(query_midi_path)
                        midi_download_str = download_button(open(query_midi_path, "rb").read(), "query.mid", "Download Query MIDI")
                        st.markdown(midi_download_str, unsafe_allow_html=True)
                    with col2:
                        uploaded_filename = midi_file.name if hasattr(midi_file, 'name') else "unknown"
                        track_name = os.path.splitext(uploaded_filename)[0]
                        query_image_path = os.path.join(IMAGES_DIR, f"{track_name}.jpg")
                        logging.info(f"Result image path: {query_image_path}")
                        if os.path.exists(query_image_path):
                            st.image(query_image_path, caption=f"Query MIDI Notes", use_column_width=True)

                if top_matches:
                    display_results(top_matches, query_midi_path, debug=debug_option)

                st.write(f"Completed processing in {time.time() - start_time:.2f} seconds.")

            except Exception as e:
                print(traceback.format_exc())
                st.error(f"Error processing MIDI file: {e}")

    with tab2:
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
                with st.container():
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        play_midi(query_midi_path)
                        midi_download_str = download_button(open(query_midi_path, "rb").read(), "query.mid", "Download Query MIDI")
                        st.markdown(midi_download_str, unsafe_allow_html=True)
                    with col2:
                        track_name = os.path.basename(query_path).split(".")[0]
                        query_image_path = os.path.join(IMAGES_DIR, f"{track_name}.jpg")
                        logging.info(f"Result image path: {query_image_path}")
                        if os.path.exists(query_image_path):
                            st.image(query_image_path, caption=f"Query MIDI Notes", use_column_width=True)

                if top_matches:
                    display_results(top_matches, query_midi_path, debug=debug_option)

            except Exception as e:
                print(traceback.format_exc())
                st.error(f"Error processing sample query: {e}")

    # "Didn't find what you're looking for?" section after both tabs
    if query_midi_path:
        st.write("### Didn't find what you're looking for?")
        st.write("Search for the track that should have matched from the library:")

        # Load the available library tracks
        library_tracks = get_sorted_files_by_mod_time(LIBRARY_DIR)

        # Create a text input for dynamic search
        search_query = st.text_input("Search for a track", "")

        # Filter the library tracks based on the search query and limit to 10 results
        filtered_tracks = [track for track in library_tracks if search_query.lower() in track.lower()][:10]

        if filtered_tracks:
            st.write("### Matching Tracks:")
            for i, track in enumerate(filtered_tracks):
                if st.button(f"Select track {i + 1}: {track}"):
                    selected_track = track
                    st.write(f"Matching against: {selected_track}")
                    selected_track_path = os.path.join(LIBRARY_DIR, selected_track)

                    # Process the selected track and get the best matches
                    try:
                        reference_pitches, reference_times = midi_to_pitches_and_times(selected_track_path)
                        reference_chunks, start_times = split_midi(reference_pitches, reference_times, 20, 18)

                        # Use best_matches function to find the closest chunk in the selected track
                        query_pitches, query_times = midi_to_pitches_and_times(query_midi_path)
                        top_matches = best_matches(query_pitches, reference_chunks, start_times, [selected_track], top_n=1)

                        # Display the best matching chunk and similarity score
                        if top_matches:
                            best_match = top_matches[0]
                            st.write(f"Best match from {selected_track}:")
                            st.write(f"Cosine Similarity: {best_match[0]:.2f}, DTW Score: {best_match[1]:.2f}, Start Time: {best_match[2]}s, Shift: {best_match[3]} semitones")

                            # Optionally play and download the matched chunk
                            best_chunk_path = find_midi_file(selected_track)
                            if best_chunk_path:
                                play_midi(best_chunk_path)
                                midi_download_str = download_button(open(best_chunk_path, "rb").read(), f"{selected_track}_best_chunk.mid", "Download Best Match MIDI")
                                st.markdown(midi_download_str, unsafe_allow_html=True)

                    except Exception as e:
                        st.error(f"Error processing the selected track: {e}")
        else:
            st.write("No tracks found.")

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
