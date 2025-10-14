#!/bin/bash
##########################################
# Script: track-cpuTemp.sh
# Track and Show CPU-temperature
# Author: haum (OTH-Regensburg, 2025)
##########################################



################## Predefinitions ##################
tDelay_s=1 # Dummy-Predefine measurement interval
nPoints=1  # Dummy-Predefine amount of datapoints
i=0        # Iteration variable (counts nPoints)
####################################################



######################## Script starts ########################
clear
echo -e "This script measures CPU-Temp and tracks that into a CSV-file. Can be used to identify CPU-throttling when rPi is not actively cooled."

### Read input-parameters
read -p "Enter your measuerment interval [s]: " tDelay_s
read -p "Enter amount of measurement points: " nPoints

echo -e "\n\nStarting readout... (Cancel with Ctrl+C)"

d=$(date +%Y_%m_%d-%H-%M-%S)
fName=${d}_CPU-Temp.csv

### Ouptut File-Header
# File-Version
echoLine="# CPU-Temp Tracking, File-Version: 1.0"
echo $echoLine
echo $echoLine >> ${fName}
# Set parameters
echoLine="# nDatapoints [#]: $nPoints"
echo $echoLine
echo $echoLine >> ${fName}
echoLine="# tInterval [s]:   $tDelay_s"
echo $echoLine
echo $echoLine >> ${fName}
# Data-Header
echoLine="# iDatapoint,Date(Y-M-D),Time(H:M:S),CPU-Temp[°C]"
echo $echoLine
echo $echoLine >> ${fName}

### Start with readout-iteration
sleep 0.01 # Give a shro
while [ $i -lt $nPoints ]; do
    ### Grab Data
    date=$(date +%Y-%m-%d)
    time=$(date +%T)
    deg=$(($(cat /sys/class/thermal/thermal_zone0/temp) / 1000))

    # Combine data into printout-Line
    dataline="$((i+1)),$date,$time,$deg"
    echo $dataline
    echo $dataline >> ${fName}
    i=$((i+1))
    sleep $tDelay_s
done

echo -e "\n\nMeasured $nPoints datapoints. Closing app, bye...\n\n"
