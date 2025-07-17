import os
import hashlib
import requests
import threading
import logging
import subprocess
import streamlit as st
from audio_processing import extract_vocals, convert_to_midi, split_midi, midi_to_pitches_and_times, process_audio, sanitize_filename, extract_midi_chunk, save_midi_chunk, is_in_library
from youtube_search import fetch_metadata_and_download, search_youtube
from download_utils import download_button
from consts import SAMPLE_QUERIES_DIR, LIBRARY_DIR, MIDIS_DIR, METADATA_DIR, LOG_DIR, CHUNKS_DIR 
import consts
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

def display_results(top_matches, query_midi_path, search_fallback=False):
    st.subheader("Top Matches:")

    for i, match in enumerate(top_matches):
        cosine_similarity_score, start_time, shift, median_diff_semitones, track, idx = match
        query_hash = hashlib.md5(track.encode()).hexdigest()
        metadata_file = os.path.join(METADATA_DIR, f"{query_hash}.txt")
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r') as f:
                video_url = f.read().strip()
            thumbnail_file = os.path.join(METADATA_DIR, f"{query_hash}.jpg")
            youtube_url = f"{video_url}&t={int(start_time)}s"
            st.markdown(f"**Match {i+1}:** [{track}]({youtube_url})")
            st.image(thumbnail_file, width=120)
            st.write(f"Cosine Similarity Score: {cosine_similarity_score:.2f}, Start time: {start_time:.2f}, Shift: {shift} semitones, Median difference: {median_diff_semitones} semitones")

            midi_path = os.path.join(MIDIS_DIR, f"{track}.mid")
            chunk = extract_midi_chunk(midi_path, start_time)
            if chunk:
                chunk_path = os.path.join(CHUNKS_DIR, f"{track}_chunk.mid")
                save_midi_chunk(chunk, chunk_path)
                midi_download_str = download_button(open(chunk_path, "rb").read(), f"{track}_chunk.mid", "Download Result MIDI Chunk")
                st.markdown(midi_download_str, unsafe_allow_html=True)
            else:
                st.write(f"No chunk extracted for track: {track}")
        else:
            if search_fallback:
                st.write(f"No metadata found for {track}, searching YouTube (Result link may not be correct)...")
                qtrack = track
                if len(track.split()) < 4:
                    qtrack = track.strip() + " Carlebach"
                video_info = search_youtube(qtrack)

                if video_info:
                    video_url = video_info['webpage_url']
                    thumbnail_url = video_info['thumbnail']
                    if not thumbnail_url.startswith('http'):
                        st.write(f"Invalid thumbnail URL: {thumbnail_url}")
                        continue
                    thumbnail_file = f"{METADATA_DIR}/{query_hash}.jpg"
                    response = requests.get(thumbnail_url)

                    with open(thumbnail_file, 'wb') as f:
                        f.write(response.content)

                    with open(metadata_file, "w") as f:
                        f.write(video_url)
                    youtube_url = f"{video_url}&t={int(start_time)}s"
                    st.markdown(f"**Match {i+1}:** [{track}]({youtube_url})")
                    st.image(thumbnail_file, width=120)
                    st.write(f"Cosine Similarity Score: {cosine_similarity_score:.2f}, Start time: {start_time:.2f}, Shift: {shift} semitones, Median difference: {median_diff_semitones} semitones")
                    midi_path = os.path.join(MIDIS_DIR, f"{track}.mid")
                    chunk = extract_midi_chunk(midi_path, start_time)
                    if chunk:
                        chunk_path = os.path.join(CHUNKS_DIR, f"{track}_chunk.mid")
                        save_midi_chunk(chunk, chunk_path)
                        midi_download_str = download_button(open(chunk_path, "rb").read(), f"{track}_chunk.mid", "Download Result MIDI Chunk")
                        st.markdown(midi_download_str, unsafe_allow_html=True)
                else:
                    st.write(f"No YouTube results found for {track}")

def process_and_add_to_library(url):
    def background_process(url, logger):
        video_infos = fetch_metadata_and_download(url, LIBRARY_DIR)
        for video_info in video_infos:
            if video_info:
                video_title = video_info['title']
                video_url = video_info['url']
                sanitized_video_title = sanitize_filename(video_title)
                mp3_file = os.path.join(LIBRARY_DIR, f"{sanitized_video_title}.mp3")
                if not is_in_library(video_url):
                    logger.info(f"Processing {video_title}...")
                    extract_vocals(mp3_file, LIBRARY_DIR)
                    vocals_path = os.path.join(LIBRARY_DIR, "htdemucs", sanitized_video_title, "vocals.wav")
                    midi_path = os.path.join(MIDIS_DIR, f"{sanitized_video_title}.mid")
                    if os.path.exists(vocals_path):
                        convert_to_midi(vocals_path, midi_path)
                    else:
                        logger.error(f"Vocals file not found for {video_title}")
                    query_hash = hashlib.md5(sanitized_video_title.encode()).hexdigest()
                    metadata_file = os.path.join(METADATA_DIR, f"{query_hash}.txt")
                    with open(metadata_file, 'w') as f:
                        f.write(video_info['url'])
                    thumbnail_url = video_info.get('thumbnail')
                    if thumbnail_url and thumbnail_url.startswith('http'):
                        thumbnail_file = os.path.join(METADATA_DIR, f"{query_hash}.jpg")
                        response = requests.get(thumbnail_url)
                        with open(thumbnail_file, 'wb') as f:
                            f.write(response.content)
                    else:
                        logger.warning(f"Invalid or missing thumbnail URL for {video_title}")
                    logger.info(f"Completed processing {video_title}")
                else:
                    logger.info(f"{video_title} is already in the library.")
            else:
                logger.error(f"Failed to fetch metadata for {url}")

    log_file = os.path.join(LOG_DIR, f"{hashlib.md5(url.encode()).hexdigest()}.log")
    logger = setup_logger("process_logger", log_file)
    threading.Thread(target=background_process, args=(url, logger)).start()
    st.write(f"Started processing {url}. Check logs for progress: {log_file}")