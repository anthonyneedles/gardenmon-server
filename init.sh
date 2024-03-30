#!/bin/bash

# Exit script on error.
set -e

if [ ! -f ./gardenmon_server.py ] ; then
	echo "ERROR: Must run in gardenmon server directory" 1>&2
	exit 1
fi

# Update apt as normal.
sudo apt update
sudo apt -y upgrade

# Install python3 and pip3.
sudo apt install python3 -y
sudo apt install python3-pip -y

# Create python virtual environment and set it up.
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt
deactivate

# Create gardenmon server service and enable to start after reboot.
sudo sh -c "sed -e 's?\${GARDENMON_SERVER_PATH}?`pwd`?g' gardenmon_server.service.template > /etc/systemd/system/gardenmon_server.service"
sudo systemctl enable gardenmon_server

# Create local options module from template. User will need to fill this out.
if [ ! -f local_options.py ]; then
    cp local_options.py.template local_options.py
    echo "local_options.py copied from template, be sure to fill out variables!"
fi
