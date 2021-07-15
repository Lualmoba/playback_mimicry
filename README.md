# Playback Mimicry

Record Vive string input and play it back through a socket. This program is intended to be used in conjunction with the mimicry_openvr package in order to obtain the correct input formatting.

## Usage
This script may be run as a stand-alone script or through the launch file.
If a launch file is used, you may specify a number of ROS parameters, otherwise
default values will be used (look at the getArgs function for default values).

Command-line usage: `vive_playback.py [mode]`

The mode parameter should be one of "`record`" or "`play`".
