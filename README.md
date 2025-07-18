# MeloDetective: Maqam Detection

## Overview

MeloDetective is a tool for detecting Middle Eastern musical modes (maqams) in audio recordings. It leverages advanced audio processing algorithms and techniques to analyze melodies and identify the most likely maqam.

![Screenshot](https://github.com/shlomota/CarleBot/assets/73965390/17536b40-8fee-462c-b6da-7dc610193e61)

## How It Works

### Step-by-Step Process

1. **Enhanced Frequency Analysis**:
   The first step involves analyzing the audio input to extract frequency information with high precision. We use advanced signal processing techniques to detect notes, which are essential for accurately identifying Middle Eastern musical modes (maqams).

2. **Note Extraction**:
   The extracted frequencies are converted into a sequence of notes. The system can detect both standard Western notes and the microtonal intervals that are characteristic of maqams.

3. **Note Normalization**:
   To ensure that the maqam detection works regardless of the absolute pitch you start on, we normalize the note sequence by subtracting the median pitch. This makes the detection pitch-independent, so it works for different vocal ranges and instruments.

4. **Pattern-Based Representation**:
   We analyze the distribution of notes in the melody, focusing on which notes are used most frequently. Each maqam has a characteristic pattern of notes that helps identify it.

5. **Maqam Matching**:
   We compare the note pattern of the input melody with the characteristic patterns of different maqams using a weighted accuracy score. This measures how well the notes in the input melody match the notes in each maqam scale, regardless of the absolute starting pitch.

   For each maqam, we try different transpositions to find the best match. The system then ranks the maqams by their similarity scores and presents the most likely matches.

6. **Maqam Library**:
   Our system includes a library of common Middle Eastern maqams, including:
   - **Ajam**: Closely resembles the Western major scale
   - **Rast**: Similar to the Western major scale but with a neutral third
   - **Nahawand**: Similar to the Western minor scale
   - **Hijaz**: Features an augmented second between the second and third degrees
   - **Kurd**: Similar to the Western Phrygian mode
   - **Bayati**: Features a neutral second degree
   - **Saba**: Features a diminished fourth
   - **Siga**: Features neutral seconds and thirds

   The library can be expanded to include additional maqams as needed.

## Directory Structure

- **app.py**: Main application script for running the MeloDetective web interface.
- **audio_processing.py**: Contains functions for processing audio files.
- **maqam_core.py**: Core functionality for working with maqams.
- **maqam_constants.py**: Constants defining maqam scales and intervals.
- **maqam_definitions.py**: Detailed definitions of maqams.
- **maqam_analysis.py**: Functions for analyzing and detecting maqams.
- **maqam_visualization.py**: Tools for visualizing maqam detection results.
- **frequency_analysis.py**: Functions for analyzing frequencies in audio.
- **data/**: Directory for storing sample queries and library files.
- **requirements.txt**: Dependencies required for running MeloDetective.

## Installation

1. **Clone the Repository**:
    ```bash
    git clone https://github.com/shlomota/MeloDetective.git -b maqam_detection
    cd MeloDetective
    ```

2. **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3. **Run the Application**:
    ```bash
    streamlit run app.py
    ```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.