import streamlit as st
import chromadb
from chromadb.config import Settings

# Initialize ChromaDB client
CHROMA_CLIENT = chromadb.Client(Settings(
    is_persistent=True,
    persist_directory="./chroma_db"
))

# Function to get or create collection
def get_or_create_collection(client, collection_name="midi_chunks"):
    try:
        collection = client.get_collection(collection_name)
    except ValueError:
        collection = client.create_collection(collection_name)
    return collection

# Initialize the collection
MIDIS_COLLECTION = CHROMA_CLIENT.get_or_create_collection("midi_chunks", metric='cosine', metadata={"hnsw:M": 64})

SAMPLE_QUERIES_DIR = "/home/ubuntu/MeloDetective/data/sample_queries"
LIBRARY_DIR = "/home/ubuntu/MeloDetective/data/library"
MIDIS_DIR = "/home/ubuntu/MeloDetective/data/midis"
METADATA_DIR = "/home/ubuntu/MeloDetective/data/metadata"
LOG_DIR = "logs"
CHUNKS_DIR = "/home/ubuntu/MeloDetective/data/chunks"

DEBUG = False

