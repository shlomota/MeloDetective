import os
import hashlib
import threading
import logging
import streamlit as st
from audio_processing import extract_vocals, convert_to_midi, split_midi, midi_to_pitches_and_times, process_audio, sanitize_filename, extract_midi_chunk, save_midi_chunk, is_in_library
from download_utils import download_button
from consts import SAMPLE_QUERIES_DIR, LIBRARY_DIR, MIDIS_DIR, LOG_DIR, CHUNKS_DIR
import numpy as np
import matplotlib.pyplot as plt
import tempfile

def setup_logger(name, log_file, level=logging.INFO):
    handler = logging.FileHandler(log_file)
    handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger

def display_path(path):
    if path:
        path_x, path_y = zip(*path)
        plt.figure(figsize=(10, 5))
        plt.plot(path_x, path_y, 'o-', markersize=2, linewidth=1)
        plt.xlabel('Query Sequence Index')
        plt.ylabel('Reference Sequence Index')
        plt.title('DTW Path')
        plt.grid(True)

        # Save plot to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
            plt.savefig(tmpfile.name)
            tmpfile_path = tmpfile.name

        # Display the plot in Streamlit
        st.image(tmpfile_path)
        plt.close()

def display_results(top_matches, query_midi_path):
    st.subheader("Top Matches:")

    for i, match in enumerate(top_matches):
        cosine_similarity_score, dtw_score, start_time, shift, path, median_diff_semitones, track = match

        st.markdown(f"**Match {i+1}:** {track}")
        st.write(f"Cosine Similarity Score: {cosine_similarity_score:.2f}, DTW Score: {dtw_score:.2f}, Start time: {start_time:.2f}, Shift: {shift} semitones, Median difference: {median_diff_semitones} semitones")

        midi_path = os.path.join(MIDIS_DIR, f"{track}.mid")
        chunk = extract_midi_chunk(midi_path, start_time)
        if chunk:
            chunk_path = os.path.join(CHUNKS_DIR, f"{track}_chunk.mid")
            save_midi_chunk(chunk, chunk_path)
            midi_download_str = download_button(open(chunk_path, "rb").read(), f"{track}_chunk.mid", "Download Result MIDI Chunk")
            st.markdown(midi_download_str, unsafe_allow_html=True)
        else:
            st.write(f"No chunk extracted for track: {track}")

        display_path(path)

def process_and_add_to_library(url):
    def background_process(url, logger):
        # Assuming URL is a direct link to an audio file; no YouTube handling
        sanitized_video_title = sanitize_filename(url)
        mp3_file = os.path.join(LIBRARY_DIR, f"{sanitized_video_title}.mp3")
        if not is_in_library(url):
            logger.info(f"Processing {sanitized_video_title}...")
            extract_vocals(mp3_file, LIBRARY_DIR)
            vocals_path = os.path.join(LIBRARY_DIR, "htdemucs", sanitized_video_title, "vocals.wav")
            midi_path = os.path.join(MIDIS_DIR, f"{sanitized_video_title}.mid")
            if os.path.exists(vocals_path):
                convert_to_midi(vocals_path, midi_path)
            else:
                logger.error(f"Vocals file not found for {sanitized_video_title}")
            logger.info(f"Completed processing {sanitized_video_title}")
        else:
            logger.info(f"{sanitized_video_title} is already in the library.")

    log_file = os.path.join(LOG_DIR, f"{hashlib.md5(url.encode()).hexdigest()}.log")
    logger = setup_logger("process_logger", log_file)
    threading.Thread(target=background_process, args=(url, logger)).start()
    st.write(f"Started processing {url}. Check logs for progress: {log_file}")
