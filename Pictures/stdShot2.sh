#!/bin/bash

# Cmd is:
# ./stdShot2 <FName> <Prefix> <SS_µs>


if [ $1 == "help" ]
then
	echo "This is the help"
	echo "Command: ./stdShot <Filename> <AG> <SS>"
	echo "<Filename>: Outputfilename"
	echo "<AG>: Analogue Gain (1.0 .. 8.0)"
	echo "<SS> ShutterSpeed/ExposureTime in microseconds (100 .. 100000)"
	exit 0
fi


pid=$(pgrep -f rPiHQCamServer2.py)
#echo "PID: $pid"
if [[ -z "$pid" ]];
then
	echo "rPiHQCamServer2.py not running. Doing your picture."
else
	echo "Closing \"rPiHQCamServer2.py\" - PID: $pid"
	kill -15 $pid
fi

ag=8.0
if [[ $# -ge 2 ]]; then
	ag=$2
fi
echo "AG=$ag"

ss=100000
if [[ $# -ge 3 ]]; then
	ss=$3
fi
echo "SS=$ss"

dtStamp=$(date -d "today" +"%y%m%d_%H%M%S")
#echo $dtStamp

echo "Taking still-image with SS=$ss"
libcamera-still -c libcamOptions.txt --gain $ag --shutter $ss -o "$dtStamp $1_SS=$ss.png"
echo "Command was: 'libcamera-still -c libcamOptions.txt --gain $ag --shutter $ss -o \"$dtStamp $1_SS=$ss.png\"'"
echo "libcamOptions.txt contains:"
cat libcamOptions.txt

