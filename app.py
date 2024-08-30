import streamlit as st
from utils import setup_logger
from midi_utils import play_midi, download_button, display_results
from file_utils import load_sample_queries
from audio_processing import process_audio
import tempfile
import os
import traceback
import consts
import time
import logging


# Set page configuration
st.set_page_config(
    initial_sidebar_state="collapsed",  # Sidebar is collapsed by default
    page_title="Niggun Detector",
)

# Ensure all required directories exist
required_dirs = [consts.LIBRARY_DIR, consts.MIDIS_DIR, consts.LOG_DIR]
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
                        st.write("Query MIDI:")
                        play_midi(query_midi_path)
                        midi_download_str = download_button(open(query_midi_path, "rb").read(), "query.mid", "Download Query MIDI")
                        st.markdown(midi_download_str, unsafe_allow_html=True)
                    with col2:
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
            finally:
                # Clean up the temporary file
                os.unlink(tmp_file_path)

    with tab2:
        st.write("Select a sample query:")
        sample_queries, sample_queries_display = load_sample_queries()

        selected_query = st.selectbox("Select a sample query", sample_queries_display)

        # Only process if a query is selected
        if selected_query != "Select your query":
            query_path = os.path.join(consts.SAMPLE_QUERIES_DIR,
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
                        st.write("Query MIDI:")
                        play_midi(query_midi_path)
                        midi_download_str = download_button(open(query_midi_path, "rb").read(), "query.mid", "Download Query MIDI")
                        st.markdown(midi_download_str, unsafe_allow_html=True)
                    with col2:
                        query_image_path = os.path.join(IMAGES_DIR, f"{track_name}.jpg")
                        logging.info(f"Result image path: {query_image_path}")
                        if os.path.exists(query_image_path):
                            st.image(query_image_path, caption=f"Query MIDI Notes", use_column_width=True)

                if top_matches:
                    display_results(top_matches, query_midi_path, debug=debug_option)
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
