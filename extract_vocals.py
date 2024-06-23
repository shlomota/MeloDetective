import os
import subprocess
import multiprocessing

# Directory containing the MP3 files
directory = "SongDetector/data/library"

# Get the number of CPU cores
num_cores = multiprocessing.cpu_count()

# Iterate over the files in the directory
for filename in os.listdir(directory):
    if filename.endswith(".mp3"):
        # Construct the full file path
        file_path = os.path.join(directory, filename)

        # Run the Demucs command for each file
        command = f"python3 -m demucs --two-stems=vocals -d cpu -j {num_cores} \"{file_path}\""
        subprocess.run(command, shell=True)

