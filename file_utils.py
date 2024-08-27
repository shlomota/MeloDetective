import os
from consts import SAMPLE_QUERIES_DIR

def get_sorted_files_by_mod_time(directory):
    # Get the list of files and their modification times
    files = [(file, os.path.getmtime(os.path.join(directory, file))) for file in os.listdir(directory) if file.endswith(('.mid', '.midi'))]
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
