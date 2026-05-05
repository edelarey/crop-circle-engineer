#!/bin/bash
# Run the Crop Circle Engineer Streamlit app
cd "$(dirname "$0")"
crop-circle-env/bin/streamlit run main.py &
sleep 2
xdg-open http://localhost:8501
