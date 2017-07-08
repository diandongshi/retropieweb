#!/usr/bin/env bash
find /opt/retropie/configs/all/emulationstation/gamelists/ -name "gamelist.xml" |xargs -i chown root:root {}
cd /home/pi/retropieweb
git pull > /dev/null 2>&1
python code.py 80
