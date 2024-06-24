#!/bin/sh
#export PYTHONPATH=/usr/lib/python3.12
#export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/local/bin"
#export PYTHONPATH=$PYTHONPATH:/home/ubuntu/.local/lib/python3.12/site-packages

cd /home/ubuntu/MeloDetective
echo $PATH
echo $PATH > /home/ubuntu/MeloDetective/log.txt
pwd >> /home/ubuntu/MeloDetective/log.txt
ls -alt >> /home/ubuntu/MeloDetective/log.txt
which python2 >> /home/ubuntu/MeloDetective/log.txt 2>&1
which python3 >> /home/ubuntu/MeloDetective/log.txt 2>&1

/usr/bin/python3 -m streamlit run app.py --server.port 8501
