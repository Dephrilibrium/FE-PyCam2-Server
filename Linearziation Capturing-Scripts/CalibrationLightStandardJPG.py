import numpy as np
import subprocess
from os.path import join, exists, isdir
from os import mkdir
from time import sleep
from picamera2 import Picamera2, Preview
from picamera2.controls import Controls
import cv2 as cv
from time import time


# List of shutters
SSs = np.linspace(start=100, stop=1000, num=10, endpoint=True).astype(np.int32)
SSs = np.hstack((SSs, np.linspace(start=2000, stop=10000, num=9, endpoint=True).astype(np.int32)))
SSs = np.hstack((SSs, np.linspace(start=12500, stop=100000, num=40-4, endpoint=True).astype(np.int32)))

# Test SSs
# SSs = np.linspace(start=92000, stop=100000, num=9, endpoint=True).astype(np.int32)
# SSs = np.linspace(start=4000, stop=70000, num=10, endpoint=True).astype(np.int32)
# SSs[0] = 114

nMean = 3

# Init
cam2 = Picamera2() # Init with all default!
pConf2 = cam2.create_preview_configuration(controls={"FrameDurationLimits": (100000, 100000)}
)
cam2.configure(pConf2)
cam2.start()
sleep(2)

realSSImgsWereTaken = []
stream="main"
folder = "/home/pi/Linearziation Capturing-Scripts/Calibration Light 1W1 Std JPGs"

if not isdir(folder):
    mkdir(folder)
    print(f"Created: {folder}")


t0 = time()
tLast = t0
ssOutput = "time since start; time of iteration; Target Set-SS; Read Meta-SS; Analogue Gain; Digital Gain; Mean(Brightness/Gains)\n"
for _ss in SSs:

    cam2.set_controls({"ExposureTime": _ss})

    sleep(1.1) # Give just enough time to change SS!
    for _iImg in range(nMean):
        main, meta = cam2.capture_arrays([stream])
        main = main[0]
        currSS = meta["ExposureTime"]
        ag = meta["AnalogueGain"]
        dg = meta["DigitalGain"]

        dGray = cv.cvtColor(main, cv.COLOR_BGRA2GRAY) # Colorimage to grayscale!
        dGray = np.divide(dGray, np.multiply(ag, dg)) # Remove gain-dependency

        meanBright =  np.mean(dGray)
        tNow = time()
        tPrintLine = f"t={tNow-t0:10.3f}; tDelta={tNow-tLast:10.3f}; TargetSS={_ss:6d}; MetaSS={currSS:6d}; AG={ag:10.3f}; DG={dg:10.3f}; MeanBright={meanBright:7.3f}"
        ssOutput += f"{tNow-t0:10.3f};{tNow-tLast:10.3f};{_ss:6d};{currSS:6d};{ag:10.3f};{dg:10.3f};{meanBright:10.3f}\n"
        print(tPrintLine)

        tLast = tNow

        realSSImgsWereTaken.append(currSS)

        # Saving
        fName = f"CalLight Gamma SS={_ss:06d}_{_iImg:04d}.jpg"
        fPath = join(folder, fName)
        cv.imwrite(fPath, dGray)
        sleep(0.15) # Be sure, that a least one frame has passed before capturing the next one!


cam2.close()

# for _iSS in range(len(realSSImgsWereTaken)):
#     _ss = SSs[_iSS // nMean]
#     _actual = realSSImgsWereTaken[_iSS]
#     ssOutput += f"{_ss}, {_actual}\n"

f = open(join(folder, "SS.log"), "w")
f.write(ssOutput)
f.close()

print("EOS")