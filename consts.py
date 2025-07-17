import os
import streamlit as st
import tempfile

# Use a platform-independent approach for data directories
# Use the current directory as the base for relative paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

# Create data directory if it doesn't exist
os.makedirs(DATA_DIR, exist_ok=True)

# Define subdirectories
SAMPLE_QUERIES_DIR = os.path.join(DATA_DIR, "sample_queries")
LIBRARY_DIR = os.path.join(DATA_DIR, "library")
MIDIS_DIR = os.path.join(DATA_DIR, "midis")
METADATA_DIR = os.path.join(DATA_DIR, "metadata")
LOG_DIR = os.path.join(DATA_DIR, "logs")
CHUNKS_DIR = os.path.join(DATA_DIR, "chunks")

# Create subdirectories if they don't exist
for dir_path in [SAMPLE_QUERIES_DIR, LIBRARY_DIR, MIDIS_DIR, METADATA_DIR, LOG_DIR, CHUNKS_DIR]:
    os.makedirs(dir_path, exist_ok=True)

DEBUG = False