#!/bin/bash

# Cmd is:
# ./stdShot2 FNamePrefix SS_µs


pid=$(pgrep -f rPiHQCamServer2.py)
#echo "PID: $pid"
if [[ -z "$pid" ]];
then
	echo "rPiHQCamServer2.py not running. Doing your picture."
else
	echo "Closing \"rPiHQCamServer2.py\" - PID: $pid"
	kill -15 $pid
fi

ss=100000
if [[ $# == 2 ]]; then
	ss=$2
fi

dtStamp=$(date -d "today" +"%y%m%d_%H%M%S")
#echo $dtStamp

echo "Taking still-image with SS=$ss"
libcamera-still -c libcamOptions.txt --shutter $ss -o "$dtStamp $1_SS=$ss.png"
echo "Command was: 'libcamera-still -c libcamOptions.txt --shutter $ss -o $1_SS=$ss.png'"
echo "libcamOptions.txt contains:"
cat libcamOptions.txt
