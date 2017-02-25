#!/usr/bin/env bash
cd /home/pi/retropieweb
git pull > /dev/null 2>&1
python code.py 80
