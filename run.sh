#!/bin/bash

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Running install_dependencies.sh first..."
    ./install_dependencies.sh
fi

# Activate the virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Run the Streamlit app
echo "Starting Maqam Detective app..."
streamlit run app.py