#!/usr/bin/python3

# Example of setting controls. Here, after one second, we fix the AGC/AEC
# to the values it has reached whereafter it will no longer change.

import time
import pickle
import os

from picamera2 import Picamera2, Preview

from _libHQCam2.ramdisk import RAMDisk
from _libHQCam2.archive import ArchiveFolder

from os.path import join, basename, dirname


def AwaitInRange(pcam, targetValue, LoDeviation=0.95, HiDeviation=1.05):

    # Get lower boundary
    if type(LoDeviation) == float:
        lo = targetValue * LoDeviation
    elif type(LoDeviation) == int:
        lo = targetValue - LoDeviation
        if lo < 0:
            lo = 0
    else:
        raise Exception("Unsupported LoDeviation type")

    # Get upper boundary
    if type(HiDeviation) == float:
        hi = targetValue * HiDeviation
    elif type(HiDeviation) == int:
        hi = targetValue + HiDeviation
    else:
        raise Exception("Unsupported HiDeviation type")


    maxIter = 10
    while maxIter > 0:
        meta = pcam.capture_metadata()
        curSS = meta["ExposureTime"]
        if curSS >= lo and curSS <= hi:
            break
        maxIter -= 1
        time.sleep(0.05)

    timedout = True if maxIter <= 0 else False


    return curSS, timedout




################ Start ######################

ramdiskPath = "/media/ramdisk/Captures"
ramdisk = RAMDisk(mntPnt=dirname(ramdiskPath))
if(not os.path.isdir(ramdiskPath)):
    os.system(f"sudo mkdir -p {ramdiskPath}")
    os.system(f"sudo chown pi:pi {ramdiskPath}")


# Cam-Tuning can be found under /usr/share/libcamera/ipa/rpi/vc4/
camTune = Picamera2.load_tuning_file("imx477_scientific.json")

# Optional settings!
gamma = Picamera2.find_tuning_algo(camTune, "rpi.contrast")
# gamma["ce_enable"] = 1                                            # Normally = 0 (deactivated)
gamma["gamma_curve"] =  [           # Linear Gamma-Curve
                        0,     0,
                     1024,  1024,
                     2048,  2048,
                     3072,  3072,
                     4096,  4096,
                     5120,  5120,
                     6144,  6144,
                     7168,  7168,
                     8192,  8192,
                     9216,  9216,
                    10240, 10240,
                    11264, 11264,
                    12288, 12288,
                    13312, 13312,
                    14336, 14336,
                    15360, 15360,
                    16384, 16384,
                    18432, 18432,
                    20480, 20480,
                    22528, 22528,
                    24576, 24576,
                    26624, 26624,
                    28672, 28672,
                    30720, 30720,
                    32768, 32768,
                    36864, 36864,
                    40960, 40960,
                    45056, 45056,
                    49152, 49152,
                    53248, 53248,
                    57344, 57344,
                    61440, 61440,
                    65535, 65535,
                ]


picam2 = Picamera2(tuning=camTune)
picam2.start_preview(Preview.NULL)

preview_config = picam2.create_preview_configuration(raw={"size": picam2.sensor_resolution})
# print(preview_config)
picam2.configure(preview_config)


picam2.start()
time.sleep(1)


metadata = picam2.capture_metadata()
controls = {c: metadata[c] for c in ["ExposureTime", "AnalogueGain", "ColourGains"]}
controls["AnalogueGain"]   = 1.0
# controls["DigitalGain"]    = 1.0
controls["ColourGains"] = (1.0, 1.0)
# print(controls)
picam2.set_controls(controls)

controlSS = {c: metadata[c] for c in ["ExposureTime"]}
SS = [
100,
200,
300,
400,
500,
600,
700,
800,
900,
1000,
1500,
2000,
2500,
3000,
3500,
4000,
4500,
5000,
5500,
6000,
6500,
7000,
7500,
8000,
8500,
9000,
9500,
10000,
12500,
15000,
17500,
20000,
22500,
25000,
27500,
30000,
32500,
35000,
37500,
40000,
42500,
45000,
47500,
50000,
52500,
55000,
57500,
60000,
62500,
65000,
67500,
70000,
72500,
75000,
77500,
80000,
82500,
85000,
87500,
90000,
92500,
95000,
97500,
100000,
]


# Preset shortest SS
startPresetSS = time.time()
_ss = SS[0]
controlSS["ExposureTime"] = _ss
picam2.set_controls(controlSS)
_ssI, to = AwaitInRange(pcam=picam2, targetValue=_ss, LoDeviation=0.85, HiDeviation=1.15)
durationPresetSS = time.time() - startPresetSS
print(str.format("Preset SS: {:.3f} - {}/{}", durationPresetSS, _ssI, _ss))




fNames = list()
ceEnabled = str(gamma["ce_enable"])
gcCurve = "lin" if gamma["gamma_curve"][2] == gamma["gamma_curve"][3] else "sciStd"
prefix = f"JSON=Sci, CE={ceEnabled}, GC={gcCurve}, PreClipBayer600x600"
for _ss in SS:
    fNames.append(join(ramdiskPath, prefix + ", SS=" + str(_ss) + ".raw"))



# Preclip-preparation
w = 600
h = 600
x1 = int((4056-w)/2)
x2 = x1 + w
y1 = int((3040-h)/2)
y2 = y1 + h

cx1 = int(x1 * 1.5) # 1.5 = 12bit / 8bit
cx2 = int(x2 * 1.5) # 1.5 = 12bit / 8bit
cy1 = int(y1) # 1.5 = 12bit / 8bit
cy2 = int(y2) # 1.5 = 12bit / 8bit

nPics = 3


print(f"Taking {len(fNames)} images on {prefix}")
logOut = ""
t0 = time.time()
durationNPics = []
for _iSS in range(len(SS)):
    _ss = SS[_iSS]

    startSetSS = time.time()
    controlSS["ExposureTime"] = _ss
    picam2.set_controls(controlSS)
    _ssI, to = AwaitInRange(pcam=picam2, targetValue=_ss, LoDeviation=0.95, HiDeviation=1.05)
    durationSetSS = time.time() - startSetSS
    print(str.format("Setting SS: {:.3f} ({}/{}) - Timeout: {}", durationSetSS, _ssI, _ss, to))

    startNPics = time.time()
    for _iImg in range(nPics): # Take 3 Images
        savName = fNames[_iSS].replace(".raw", str.format(", #={:02d}.raw", _iImg))
        # print("Capturing: " + fNames[_iSS])
        print("Capturing: " + savName)
        startCap = time.time()
        # metadata = picam2.capture_metadata()
        metadata = picam2.capture_metadata()
        raw = picam2.capture_array("raw")
        raw = raw[cy1:cy2, cx1:cx2]
        durationCap = time.time() - startCap
        print(str.format("Capture took:  {}s", durationCap))
        # print(raw.shape)

        startSav = time.time()
        f = open(savName, "wb")
        # f = open(fNames[_iSS], "wb")
        pickle.dump(raw, f)
        f.close()
        durationSav = time.time() - startSav
        durationCapSav = time.time() - startCap

        print(str.format("Pickle need: {}s", durationSav))
        print(str.format("Capture + Save: {}s", durationCapSav))

        _curSS = metadata["ExposureTime"]
        _fps = 1 / (metadata["FrameDuration"] * 1e-6)
        logOut += str.format("fName:\"{}\";FPS:{:.3f};ssSoll:{};ssIst:{};tCap:{:.3f};tSav:{:.3f};tCapSav:{:.3f};tSetSS:{:.3f}\n", fNames[_iSS], _fps, _ss, _curSS, durationCap, durationSav, durationCapSav, durationSetSS)
    durationNPics.append(time.time() - startNPics)
    print(str.format("{} Pics@SS={} took {:.3f}s", nPics, _ss, durationNPics[-1]))

durationOverallCapSav = time.time() - t0
print(str.format("Overall Capture & Save took: {}s", durationOverallCapSav))

startCompress = time.time()
ArchiveFolder(ramdiskPath, join(dirname(ramdiskPath), prefix + ".tar.gz"), compress=True, SuppressParents=True, Multicore=True)
durationCompress = time.time() - startCompress
print(str.format("Compressed in: {:.3f}s", durationCompress))

durationAllInAll = time.time() - t0
print(str.format("All in all: {:.3f}s", durationAllInAll))


for _iNPics in range(len(durationNPics)):
    _ss = SS[_iNPics]
    _tNPics = durationNPics[_iNPics]
    logOut += str.format("{} Pics@SS={} took {:.3f}s\n", nPics, _ss, _tNPics)
logOut += str.format("tOverallCapSave:{:.3f};tCompress:{:.3f};tAllInAll:{:.3f}", durationOverallCapSav, durationCompress, durationAllInAll)


print(str.format("Saving log {}".ljust(60), join(dirname(ramdiskPath), prefix + ".log")), end="")
f = open(join(dirname(ramdiskPath), prefix + ".log"), "w")
f.writelines(logOut)
f.close()
print("Ok")
print("Finished")