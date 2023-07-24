#!/bin/bash

pid=$(pgrep -f rPiHQCamServer2.py)
#echo "PID: $pid"
if [[ -z "$pid" ]];
then
	echo "rPiHQCamServer2.py not running. Doing your video."
else
	echo "Closing \"rPiHQCamServer2.py\" - PID: $pid"
	kill -15 $pid
fi

ss=10000
if [[ $# > 1 ]]; then
	ss=$2
fi

to=5000
if [[ $# > 2 ]]; then
	to=$3
fi

echo "Taking video with SS=$ss"
libcamera-vid -c libcamVidOptions.txt --shutter=$ss --timeout=$to -o $1_SS=10000.h264
echo "Command was: 'libcamera-vid -c libcamVidOptions.txt --shutter=$ss --timeout=$to -o $1_SS=$ss.h264'"
echo "libcamOptions.txt contains:"
cat libcamVidOptions.txt
