import streamlit as st
from utils import setup_logger
from midi_utils import play_midi, download_button, display_results, find_midi_file
from file_utils import load_sample_queries, get_sorted_files_by_mod_time
from audio_processing import process_audio
from match_midi_agnostic import best_matches, midi_to_pitches_and_times, split_midi, weighted_dtw
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
    tab1, tab2, tab3 = st.tabs(["Upload MIDI", "Use a Sample", "Compare Two Melodies"])

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

    # Compare Two Melodies tab
    with tab3:
        st.write("### Upload Two MIDI Files to Compare")

        query_file = st.file_uploader("Upload the query MIDI file (first file)", type=['mid', 'midi'], key='query')
        reference_file = st.file_uploader("Upload the reference MIDI file (second file)", type=['mid', 'midi'], key='reference')

        if query_file is not None and reference_file is not None:
            try:
                # Save query and reference files to temporary files
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mid") as tmp_query:
                    tmp_query.write(query_file.getvalue())
                    query_path = tmp_query.name

                with tempfile.NamedTemporaryFile(delete=False, suffix=".mid") as tmp_reference:
                    tmp_reference.write(reference_file.getvalue())
                    reference_path = tmp_reference.name

                # Extract pitches and times for both files
                query_pitches, query_times = midi_to_pitches_and_times(query_path)
                reference_pitches, reference_times = midi_to_pitches_and_times(reference_path)

                # Perform DTW comparison between the two files
                st.write("### Comparing the two melodies...")
                distance, path = weighted_dtw(query_pitches, reference_pitches)

                # Display similarity result
                st.write(f"DTW Distance between the two melodies: {distance:.2f}")

                # Optionally play the uploaded files
                st.write("### Listen to the Query and Reference MIDI:")
                col1, col2 = st.columns([1, 1])

                with col1:
                    st.write("Query MIDI:")
                    play_midi(query_path)

                with col2:
                    st.write("Reference MIDI:")
                    play_midi(reference_path)

            except Exception as e:
                st.error(f"Error comparing the two MIDI files: {e}")

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
