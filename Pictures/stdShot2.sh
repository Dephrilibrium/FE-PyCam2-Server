#!/bin/bash

pid=$(pgrep -f rPiHQCamServer2.py)
#echo "PID: $pid"
if [[ -z "$pid" ]];
then
	echo "rPiHQCamServer2.py not running. Doing your picture."
else
	echo "Closing \"rPiHQCamServer2.py\" - PID: $pid"
	kill -15 $pid
fi

ss=10000
if [[ $# == 2 ]]; then
	ss=$2
fi

echo "Taking still-image with SS=$ss"
libcamera-still -c libcamOptions.txt --shutter $ss -o $1_SS=$ss.png
echo "Command was: 'libcamera-still -c libcamOptions.txt --shutter $ss -o $1_SS=$ss.png'"
echo "libcamOptions.txt contains:"
cat libcamOptions.txt