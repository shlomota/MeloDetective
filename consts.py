import streamlit as st
SAMPLE_QUERIES_DIR = "/home/ubuntu/MeloDetective/data/sample_queries"
LIBRARY_DIR = "/home/ubuntu/MeloDetective/data/library"
MIDIS_DIR = "/home/ubuntu/MeloDetective/data/midis"
METADATA_DIR = "/home/ubuntu/MeloDetective/data/metadata"
LOG_DIR = "logs"
CHUNKS_DIR = "/home/ubuntu/MeloDetective/data/chunks"

# Check if 'debug' parameter is set to '1'
query_params = st.experimental_get_query_params()
DEBUG = False
if query_params.get('debug') == ['1']:
    DEBUG = True
