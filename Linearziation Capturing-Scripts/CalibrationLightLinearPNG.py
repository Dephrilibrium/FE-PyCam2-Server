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
# SSs[0] = 114

# SSs = np.linspace(start=4000, stop=80000, num=6, endpoint=True).astype(np.int32)  # Test SSs (checking AG, DG behaviour)

nMean = 3

# Init
tuningNoir = Picamera2.load_tuning_file("imx477_scientific.json")
cam2 = Picamera2(tuning=tuningNoir)
pConf2 = cam2.create_preview_configuration(raw={"size": cam2.sensor_resolution},
                                             controls={ "AnalogueGain":      1.0,
                                                        "FrameDurationLimits": (100000, 100000),
                                                    }
)
cam2.configure(pConf2)
cam2.start()
sleep(2)

realSSImgsWereTaken = []
stream="raw"
folder = "/home/pi/Linearziation Capturing-Scripts/Calibration Light 1W1 Noir PNGs"

if not isdir(folder):
    mkdir(folder)
    print(f"Created: {folder}")

imH = 3040
imW = 4056
bayW = int(imW * 1.5)

t0 = time()
tLast = t0
ssOutput = "time since start; time of iteration; Target Set-SS; Read Meta-SS; Analogue Gain; Digital Gain; Mean(Brightness/Gains)\n"
for _ss in SSs:

    cam2.set_controls({"ExposureTime": _ss})

    # # SS-Check
    # ssOk = False
    # loSS = 0.85 * _ss   # Lower bound
    # hiSS = 1.15 * _ss   # Upper bound
    # while not ssOk:
    #     currSS = cam2.capture_metadata()["ExposureTime"]
    #     if currSS <= hiSS and currSS >= loSS:
    #         ssOk = True
    #     print(f"Current SS: {currSS}".ljust(50), end="\r")
    #     sleep(0.1)

    sleep(1.1) # Takes 0.9s @ 10FPS
    for _iImg in range(nMean):
        raw, meta = cam2.capture_arrays(["raw"])
        raw = raw[0].astype(np.uint16)
        currSS = meta["ExposureTime"]
        ag = meta["AnalogueGain"]
        dg = meta["DigitalGain"]

        raw = raw[:, :bayW].astype(np.uint16)
        dMosaic = np.zeros((imH, imW), dtype=np.uint16)
        for byte in range(2):
            dMosaic[:, byte::2] = ( (raw[:, byte::3] << 4) | ((raw[:, 2::3] >> (byte * 4)) & 0b1111) )
        # raw = dMosaic

        # dMosaic = np.divide(dMosaic, np.multiply(ag, dg)) # AG=DG=1.0!
        dMosaic = np.right_shift(dMosaic, 4) # Make 8-Bit image for comparison

        meanBright =  np.mean(dMosaic)
        tNow = time()
        tPrintLine = f"t={tNow-t0:10.3f}; tDelta={tNow-tLast:10.3f}; TargetSS={_ss:6d}; MetaSS={currSS:6d}; AG={ag:10.3f}; DG={dg:10.3f}; MeanBright={meanBright:7.3f}"
        ssOutput += f"{tNow-t0:10.3f};{tNow-tLast:10.3f};{_ss:6d};{currSS:6d};{ag:10.3f};{dg:10.3f};{meanBright:10.3f}\n"
        print(tPrintLine)

        tLast = tNow

        realSSImgsWereTaken.append(currSS)

        # Saving
        fName = f"CalLight Linear SS={_ss:06d}_{_iImg:04d}.png"
        fPath = join(folder, fName)
        dSave = dMosaic.astype(np.uint8)
        cv.imwrite(fPath, dSave)
        # sleep(0.15)


cam2.close()

f = open(join(folder, "SS.log"), "w")
f.write(ssOutput)
f.close()

print("EOS")