#!/bin/bash
# Args: stdVideo2.sh Filename Shutterspeed_µs RecordTime_s

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

ss=10000
if [[ $# -ge 3 ]]; then
	ss=$3
fi

to=5000
if [[ $# > 4 ]]; then
	to=$4
fi

dtStamp=$(date -d "today" +"%y%m%d_%H%M%S")
#echo $dtStamp

echo "Taking video with SS=$ss"
libcamera-vid -c libcamVidOptions.txt --gain=$ag --shutter=$ss --timeout=$to -o "$dtStamp $1_SS=10000.h264"
echo libcamera-vid -c libcamVidOptions.txt --gain=$ag --shutter=$ss --timeout=$to -o \"$dtStamp $1_SS=10000.h264\"'"
echo "libcamOptions.txt contains:"
cat libcamVidOptions.txt
