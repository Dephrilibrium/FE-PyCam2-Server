#!/bin/bash
# Args: stdVideo2.sh <Filename> <AG> <Shutterspeed_µs> <RecordTime_s>

if [ $1 == "help" ]
then
	echo "This is the help. Arguments are in order:"
	echo "<Filename>: String to the target file."
	echo "<AG>: Analogue Gain (valid range: 1.0 .. 8.0)"
	echo "<Shutterspeed_µs>: The exposure time in microseconds."
	echo "<RecordTime_s>: Time the video is recorded."
	exit 0
fi


pid=$(pgrep -f rPiHQCamServer2.py)
#echo "PID: $pid"
if [[ -z "$pid" ]];
then
	echo "rPiHQCamServer2.py not running. Doing your video."
else
	echo "Closing \"rPiHQCamServer2.py\" - PID: $pid"
	kill -15 $pid
fi


ag=8.0
if [[ $# -ge 2 ]]; then
	ag=$2
fi
echo "AG=$ag"

ss=10000
if [[ $# -ge 3 ]]; then
	ss=$3
fi
echo "SS=$ss"

to=5000
if [[ $# > 4 ]]; then
	to=$4
fi
echo "TimeOut=$to"

dtStamp=$(date -d "today" +"%y%m%d_%H%M%S")
#echo $dtStamp

echo "Taking video with SS=$ss"
libcamera-vid -c libcamVidOptions.txt --gain=$ag --shutter=$ss --timeout=$to -o "$dtStamp $1_SS=10000.h264"
echo libcamera-vid -c libcamVidOptions.txt --gain=$ag --shutter=$ss --timeout=$to -o \"$dtStamp $1_SS=10000.h264\"'"
echo "libcamOptions.txt contains:"
cat libcamVidOptions.txt
