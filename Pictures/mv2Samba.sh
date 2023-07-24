#!/bin/bash

sudo mount -a

echo Trying to move Logs
sudo mv ./*.log /mnt/Samba/Hausladen/YawCam/

echo Trying to move JPGs
sudo mv ./*.jpg /mnt/Samba/Hausladen/YawCam/

echo Trying to move PNGs
sudo mv ./*.png /mnt/Samba/Hausladen/YawCam/

echo Trying to move h264
sudo mv ./*.h264 /mnt/Samba/Hausladen/YawCam/


