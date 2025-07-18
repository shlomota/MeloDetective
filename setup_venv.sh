#!/bin/bash

# Create and activate a virtual environment
echo "Creating virtual environment..."
python -m venv venv
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install basic dependencies
echo "Installing basic dependencies..."
pip install numpy pandas tqdm matplotlib mido librosa streamlit pydub midiutil

# Install Basic Pitch
echo "Installing Basic Pitch..."
pip install basic-pitch

# Install optional dependencies for visualization
echo "Installing optional dependencies for visualization..."
pip install fortepyan streamlit-pianoroll

# Install microphone recording support
echo "Installing microphone recording support..."
pip install streamlit-mic-recorder

echo "Setup complete! Activate the virtual environment with:"
echo "source venv/bin/activate"