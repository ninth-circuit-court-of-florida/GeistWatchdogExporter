#!/usr/bin/env bash
# Update this for the location you want
source /home/$USER/.profile
cd /home/$USER/GeistWatchdogExporter
date > run.last
pgrep -f collector 1>/dev/null 2>&1 || /usr/bin/python3 collector.py > app.log
