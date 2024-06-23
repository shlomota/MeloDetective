#!/bin/sh
export PYTHONPATH=/usr/lib/python3.12
cd /home/ubuntu/SongDetector
echo $PATH
echo $PATH > /home/ubuntu/SongDetector/log.txt
/usr/bin/python3 -m streamlit run app.py --server.port 8501
