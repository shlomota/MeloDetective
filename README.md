# MeloDetective: Tracing Origins Of Tunes

## Demo

Check out the live demo of MeloDetective at [carlebot.us](http://carlebot.us).


![Screenshot](https://github.com/shlomota/CarleBot/assets/73965390/17536b40-8fee-462c-b6da-7dc610193e61)

## Overview

MeloDetective is a tool for locating tunes in audio recordings. It leverages advanced audio processing algorithms and techniques to analyze and match melodies. This project uses a combination of Demucs, the Melodia algorithm, and Dynamic Time Warping (DTW) to achieve accurate results.

## How It Works

### Step-by-Step Process

1. **Extract Vocals**:
    - **Demucs**: MeloDetective uses [Demucs](https://github.com/facebookresearch/demucs) to separate vocals from the accompaniment in an audio recording. Demucs is a state-of-the-art music source separation tool.

2. **Convert to MIDI**:
    - **Melodia Algorithm**: The extracted vocal track is processed using the [Melodia](https://github.com/justinsalamon/audio_to_midi_melodia) algorithm to convert the melody to a MIDI file. This algorithm gave me the most stable results for converting singing to midi. Some other options include [Basic-Pitch](https://github.com/spotify/basic-pitch) [YIN](https://github.com/brentspell/torch-yin) and more.

3. **Split into Overlapping Chunks**:
    - The MIDI file is split into overlapping chunks to facilitate detailed analysis. Each chunk is normalized to make it key-agnostic, allowing for more robust matching.

4. **Find Matches with DTW**:
    - **Dynamic Time Warping (DTW)**: MeloDetective uses an adaptation of DTW to compare the query MIDI chunks with the reference library. DTW is an algorithm used to measure similarity between two time series sequences, which can vary in speed. This makes it ideal for matching melodies that might have tempo variations.

## High-Level View

1. **Reference Preparation**: Prepare a library of reference MIDI files using Demucs and the Melodia algorithm. This step involves extracting vocals from songs and converting these vocal tracks into MIDI format.

2. **Query Processing**: When a new audio query is received, it undergoes the same processing steps as the reference preparation. The query is separated into vocals, converted to MIDI, and split into chunks.

3. **Matching**: Each chunk of the query is compared against the reference library using DTW. This comparison identifies the closest matching melodies in the reference library.

4. **Results**: The best matches are presented to the user, showing which segments of the query correspond to known tunes.

## Directory Structure

- **app.py**: Main application script for running the MeloDetective web interface.
- **audio_processing.py**: Contains functions for processing audio files.
- **audio_to_midi_melodia**: Directory containing scripts for running the Melodia algorithm (Python 2 required).
- **midi_chunk_processor.py**: Script for matching MIDI files using the library.
- **data/**: Directory for storing sample queries, library files, and metadata.
- **logs/**: Directory for storing log files.
- **utils.py**: Utility functions used across the project.
- **requirements.txt**: Dependencies required for running MeloDetective.
- **youtube_search.py**: Script for fetching metadata and downloading YouTube audio.

## Installation

1. **Clone the Repository**:
    ```bash
    git clone https://github.com/yourusername/MeloDetective.git
    cd MeloDetective
    ```

2. **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3. **Setup Melodia**:
    - Ensure Python 2 is installed and run the `audio_to_midi_melodia` script using Python 2.

4. **Run the Application**:
    ```bash
    streamlit run app.py
    ```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
