# Global libs
import os
from os.path import join, basename, dirname, isdir, isfile
from time import time, sleep

import socket
import pickle
import numpy as np


# Custom libs
from _libHQCam2.archive import ArchiveFolder #, CompressFolder
from _libHQCam2.ramdisk import RAMDisk, CreateFolder4User

from _libHQCam2.misc import duration, how_long, DecodeBoolStr
from _libHQCam2.Logger import StdOutLogger, LogLineLeft, LogLineLeftRight

from picamera2.controls import Controls
from _libHQCam2.PiCam2 import PiCam2





### Defaults
# Paths
ramdisk = None
SDCardPath = r"/home/pi/Pictures/Captures"
mntPnt_RAMDisk = r"/media/ramdisk"                # Mounting Point of ramdisk; Comment out to avoid a RAMDISK

imFolderPath = join(mntPnt_RAMDisk, "Captures")      # Is created within the capSeq_Path

# Static responses
ackStr = "ack"
nakStr = "nak"

# Server settings
port = 5060
servSock = None         # Obj-Variable for socket
servConn = None         # Obj-Variable for client-connection

# Camera settings
# See also into SetupCamera2
cam = None              # Obj-Variable for PiCam2


# Server settings
srvr_ClipWinBayer = [1500,1500]             # Can be [(offsetX, offsetY, )windowWidth, windowHeight] || Without optional offsets the clip is around the center
srvr_DemosaicClippedBayerImgs = False
srvr_ShrinkHalfDemosaicedIterations = 0


# Logger (can be used optional)
# logFilePath = "/home/pi/RPiHQCam2.log"
logger = None









# Local Server-Functions
def SetupServer():
    LogLineLeft("Creating socket")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # SO_REUSEADDR=1: Allow reuse when socket-port already exists
    print("ok")
    LogLineLeft("Binding socket")
    try:
        s.bind(('', port))
    except socket.error as msg:
        print(msg)
    print("ok")
    return s



def AwaitIncomingConnection(socket):
    print("Awaiting connection request from client...")
    socket.listen(5)  # Allow up to 5 connections
    sConn, connIP = socket.accept()
    LogLineLeftRight("Client connected:", f"{connIP[0]}:{connIP[1]}")
    return sConn



def SetupCamera2(fr=10.0):
    global cam

    # Init PiCam2
    cam = PiCam2(fr=fr)
    LogLineLeftRight("Reading IDN:", cam.IDN())
    return





def IDN():
    return cam.IDN()


def ECHO(payloadArr):
    return " ".join(payloadArr)


def Server_ClipWinBayerImage(ClipWinBayerByServer):
    global srvr_ClipWinBayer

    clpWin = [int(val) for val in ClipWinBayerByServer.split(":")]
    nVals = len(clpWin)
    if nVals == 2 or nVals == 4:
        srvr_ClipWinBayer = clpWin
        return ackStr

    return nakStr

def Server_DemosaicClippedBayerImgs(DebayerByServer):
    global srvr_DemosaicClippedBayerImgs

    srvr_DemosaicClippedBayerImgs = DecodeBoolStr(DebayerByServer)
    if not srvr_DemosaicClippedBayerImgs:                # Shrinking needs debayered data
        Server_ShrinkHalfDemosaicedIterations("0")
    return ackStr

def Server_ShrinkHalfDemosaicedIterations(ShrinkHalfIterations):
    global srvr_ShrinkHalfDemosaicedIterations

    srvr_ShrinkHalfDemosaicedIterations = int(ShrinkHalfIterations)

    if srvr_ShrinkHalfDemosaicedIterations < 0:
        srvr_ShrinkHalfDemosaicedIterations = 0
        # raise Exception("ShrinkHalf - Can't iterate negative.") # Old

    if srvr_ShrinkHalfDemosaicedIterations > 0:         # For shrinking, data must be debayered!
        Server_DemosaicClippedBayerImgs("1")
    return ackStr


# def Server_Compress(compressPath:str, tarGzFName:str, Multicore=True, SuppressParents=True):
#     sCmprss = time()
#     retVal = CompressFolder(compressPath, tarGzFName, Multicore, SuppressParents)
#     how_long(sCmprss, "Compressing")    
#     return ackStr if retVal == 0 else nakStr


def Server_Archive(archiveFolderPath:str, archiveFName:str, compress=True, multicore=True, suppressParents=True):
    sCmprss = time()
    retVal = ArchiveFolder(archiveFolderPath, archiveFName, compress, multicore, suppressParents)
    how_long(sCmprss, "Archiving" + ("+Compression" if compress else ""))
    return ackStr if retVal == 0 else nakStr


def ConfAwait(tVal, SetFunc, GetFunc, LoBnd=0.95, HiBnd=1.05, IterMax=10):

    SetFunc(tVal)
    try:
        valIsList = True
        _ = (e for e in tVal)
    except TypeError:
        valIsList = False
        tVal = [tVal]
    
    # Do the checks
    nVals = len(tVal)
    vInRange = [False] * nVals
    # start = time()
    while IterMax > 0:
        cVal = GetFunc()
        for _iVal in range(len(tVal)):
            _tVal = tVal[_iVal]
            lo = _tVal * LoBnd
            hi = _tVal * HiBnd
            
            if valIsList:
                _cVal = cVal[_iVal]
            else:
                _cVal = cVal

            if _cVal >= lo and _cVal <= hi:
                vInRange[_iVal] = True
            # sleep(0.05) # GetFunc always gets via cam.capture_metadata() which waits for a frame
        
        if _iVal == (nVals-1) and all(vInRange):
            break
        IterMax -= 1
    # how_long(start, "inner loop")

    timedout = True if IterMax <= 0 else False

    return cVal, timedout

def ConfShutterspeed(tVal, LoBnd=0.95, HiBnd=1.05):
    start = time()
    tVal = int(tVal)
    
    # startSet = time()
    # cam.SetSS(tVal)
    # cam.GetCamera().set_controls({"ExposureTime": tVal})
    # how_long(startSet, "SetSS")

    # startCheck = time()
    # i = 0
    # metadata = cam.GetCamera().capture_metadata() # dauert immer einen frame -> 1/fps
    # cur_ss = metadata["ExposureTime"]
    # while tVal<(cur_ss*0.95) or tVal>(cur_ss*1.05):
    #     # time.sleep(0.02)
    #     #start_loop=time.time()
    #     metadata = cam.GetCamera().capture_metadata() # dauert immer einen frame -> 1/fps
    #     cur_ss = metadata["ExposureTime"]
    #     #start_loop=how_long(start_loop, 'Schleife')
    #     print('ist: '+str(cur_ss)+', It: '+str(i))
    #     i = i + 1
    # how_long(startCheck, "SS await")
    # how_long(start, str.format("SS-Change S:{}, I:{} - Timeout:{}", tVal, cur_ss, False))

    cVal, TO = ConfAwait(tVal, cam.SetSS, cam.GetSS, LoBnd=LoBnd, HiBnd=HiBnd, IterMax=15)
    # how_long(startCheck, "SS await")
    how_long(start, str.format("SS-Change S:{}, I:{} - Timeout:{}", tVal, cVal, TO))
    return ackStr

def ConfAnalogGain(tVal="1.0"):
    start = time()
    tVal = float(tVal)
    cVal, TO = ConfAwait(tVal, cam.SetAG, cam.GetAG)
    how_long(start, str.format("AG-Change S:{}, I:{} - Timeout:{}", tVal, cVal, TO))
    return ackStr

def ConfWhiteBalance(tVal="1.0:1.0"):
    start = time()
    tVal = [float(v) for v in tVal.split(":")]
    cVal, TO = ConfAwait(tVal, cam.SetAWB, cam.GetAWB)
    how_long(start, str.format("AWB-Change S:{}, I:{} - Timeout:{}", tVal, cVal, TO))
    return ackStr


def ConfScalerCrop(offsetXY="0:0", sizeWH="4056:3040"):
    start = time()
    offsetXY = list(offsetXY.split(":"))
    sizeWH = list(sizeWH.split(":"))
    tVal = [int(v) for v in offsetXY + sizeWH]
    cVal, TO = ConfAwait(tVal, cam.SetScalerCrop, cam.GetScalerCrop)
    how_long(start, str.format("ScalerCrop-Change S:{}, I:{} - Timeout:{}", tVal, cVal, TO))
    return ackStr

def ConfFramerate(FR="10.0"):
    start = time()
    tVal = float(FR)
    cVal, TO = ConfAwait(tVal, cam.SetFR, cam.GetFR)
    how_long(start, str.format("FrameRate-Change S:{}, I:{} - Timeout:{}", tVal, cVal, TO))
    return ackStr




def CaptureShutterspeedSequence(Prefix, StorePath, SS="1000:3150:10000:31500", nPics=3, tMax=3.0, SaveSSLog=True):
    global cam, srvr_ClipWinBayer # Used for presetting SS

    SS = [int(_ss) for _ss in SS.split(":")]    # ShutterSpeeds -> int
    nPics = int(nPics)                          # nPics -> int
    tMax = float(tMax)                          # TimeMax (interval) -> float
    SaveSSLog = DecodeBoolStr(SaveSSLog)                 # SaveSSLog (True/False, 1/0, yes/no) -> bool
    if StorePath == None or StorePath == "":
        raise Exception("CaptureSequence() - No storage-path given.")

    if SaveSSLog:
        ssLogStr = ""

    ####### Calculate crop-coordinates #######
    w32 = 4064          # Captured array-Width   aligned to 32
    h16 = 3040          # Captured array-Height  aigned to 16
    if len(srvr_ClipWinBayer) == 2: # Only Size is given!
        w4k = 4056          # Px-Width               of raw bayer-data
        h4k = 3040          # Px-Height              of raw bayer-data
        wWin = srvr_ClipWinBayer[0]   # Is window-Px-Width  when only size is given
        hWin = srvr_ClipWinBayer[1]   # Is window-Px-Height when only size is given

        x1 = (w4k - wWin) // 2
        y1 = (h4k - hWin) // 2
    else: # Offset + Size given
        wWin = srvr_ClipWinBayer[2]   # Is window-Px-Width  when offset + size is given
        hWin = srvr_ClipWinBayer[3]   # Is window-Px-Height when offset + size is given
        x1 = srvr_ClipWinBayer[0]     # Is offsetX          when offset + size is given
        y1 = srvr_ClipWinBayer[1]     # Is offsetY          when offset + size is given
    
    x2 = x1 + wWin
    y2 = y1 + hWin

    if srvr_ClipWinBayer:
        cx1 = int(x1 * 1.5) # * 1.5 (12bit / 8bit)
        cx2 = int(x2 * 1.5) # * 1.5 (12bit / 8bit)
        cy1 = int(y1)       # / 1 = Height not affected by bit-size
        cy2 = int(y2)       # / 1 = Height not affected by bit-size

    ####### Take the pictures #######
    sSeq = time()
    cntSS = len(SS)
    for _iSS in range(cntSS):
        _tSS = SS[_iSS] # Grab ss directly from list

        _ack, _cSS, _TO = ConfShutterspeed(_tSS)


        ### Build filenames ###
        fNames = []
        for _iPic in range(nPics): # Prepare filenames
            fName = str.format("{}_ss={}_{}.{}", Prefix, _tSS, str(_iPic).zfill(4), "raw" )
            fNames.append(join(StorePath, fName))


        ### Raw-capture the images into a list ###
        raws = []
        if SaveSSLog:
            rawMetas = []
        dCaps = []
        sCapAll = time()
        for _iPic in range(nPics):
            sCap = time()
            raw, meta = cam.GetCamera().capture_arrays(["raw"])
            raws.append(raw[0])
            if SaveSSLog:
                rawMetas.append(meta)
            dCaps.append(duration(sCap))
            print(f"Capturing {fNames[_iPic]} took {dCaps[-1]:.3f}")
        dCapAll = duration(sCapAll)
        print(f"Raw Capturing of SS-Sequence took {dCapAll:.3f}")

        ### Preset to next SS, so that the camera settles during the following code runs ###
        if _iSS < (cntSS-1): # Preset only, if not already the last SS -> set back to SS[0] at the end of this method
            LogLineLeftRight(f"Presetting SS={SS[_iSS + 1]}:", "ok")
            cam.SetSS(SS[_iSS + 1])


        ### Do post-processing to the images ###
        sPostProcessingAll = time()
        dPostProcessings = []
        for _iPic in range(nPics):
            sPostProcessing = time()
            raw = raws[_iPic]               # Grab current image as numpy
            raw = raw[cy1:cy2, cx1:cx2]     # Preclip bayer data to reduce the amount of data to handle
            raw = raw.astype(np.uint16)     # Target-Type needs to be uint16. uint8 can clip the 4 upper MSB when shifting up

            if srvr_DemosaicClippedBayerImgs:                    # Debayer residual data
                dMosaic = np.zeros((hWin, wWin), dtype=np.uint16)
                for byte in range(2):
                    dMosaic[:, byte::2] = ( (raw[:, byte::3] << 4) | ((raw[:, 2::3] >> (byte * 4)) & 0b1111) )
                raw = dMosaic
                
            if srvr_ShrinkHalfDemosaicedIterations > 0:
                # raw = (raw[::2, ::2] + raw[1::2, ::2] + raw[::2, 1::2] + raw[1::2, 1::2]) # Old code without saturation detection
                # Reduce resolution of image and mask to 507x380 by addition ( //4 für Mittelung)
                satBright=0xFFF           # 0xFFF = (2**12)-1 = Maximum Sensor-Value = Saturation
                satMask = (raw >= satBright) #  mark saturated pixels
                for _iShrinkIter in range(srvr_ShrinkHalfDemosaicedIterations): # Combines 2x2 Pxls per iteration!
                    satMask = (satMask[::2, ::2] | satMask[1::2, ::2] | satMask[::2, 1::2] | satMask[1::2, 1::2])
                    raw = (raw[::2, ::2] + raw[1::2, ::2] + raw[::2, 1::2] + raw[1::2, 1::2]) #// 4 #jeweils halbiert
                raw[satMask]=0xFFFF         # 0xFFFF = (2**16)-1 = Maximum uint16-value to clearly mark saturated pixels

            dPostProcessings.append(duration(sPostProcessing))
            fName = fNames[_iPic]
            print(f"PostProcessing {fName} took {dPostProcessings[-1]:.3f}")

        dPostProcessingAll = duration(sPostProcessingAll)
        print(f"All Post-processing took {dPostProcessingAll:.3f}")

        ### Saving the postprocessed images ###
        for _iPic in range(nPics):
            fName = fNames[_iPic]
            sSav = time()
            f = open(fName, "wb")
            pickle.dump(raw, f)
            f.close()
            dSav = duration(sSav)
            print(f"Saving {fName} took {dSav:.3f}")

            if SaveSSLog:
                _cSS  = rawMetas[_iPic]["ExposureTime"]
                _fd   = rawMetas[_iPic]["FrameDuration"]
                _dCap = dCaps[_iPic]
                ssLogStr += str.format("fName:{};tCap:{:.3f};tSav{:.3f};sSS:{};iSS:{};FD:{}\n", fName, _dCap, dSav, _tSS, _cSS, _fd)
    how_long(sSeq, "Entire CaptureShutterspeedSequence")

    LogLineLeftRight(f"Presetting SS={SS[0]}:", "ok")
    cam.SetSS(SS[0]) # Preset the fastest SS for next call
    # Save the SS-Log
    if SaveSSLog:
        f = open(join(StorePath, f"{Prefix}_SSCapture.log"), "w")
        f.writelines(ssLogStr)
        f.close()
    return ackStr




### Start script ###
# Init logger if wanted
if "logFilePath" in locals():
    logger = StdOutLogger(logFilePath)


# (Re-)Create RAMDisk
if "mntPnt_RAMDisk" in locals() and mntPnt_RAMDisk != None:
    sRAMDisk = time()
    if(not isdir(mntPnt_RAMDisk)):
        os.system(f"mkdir -p {mntPnt_RAMDisk}")
    ramdisk = RAMDisk(mntPnt_RAMDisk)
    CreateFolder4User(imFolderPath)

    LogLineLeftRight("Setup RAMDisk took", f"{duration(sRAMDisk):.3f}s")




# Create Camera
SetupCamera2(10.0)
# CaptureShutterspeedSequence("test", imFolderPath, "1000:3150:10000:31500") # Testmethod

# (Re-)Create Server
sServer = time()
servSock = SetupServer()
LogLineLeftRight("Server set up in: ", f"{duration(sServer):.3f}s")
servConn = AwaitIncomingConnection(servSock)


# Run main server-loop
LogLineLeftRight("Starting main server-loop", "ok")
keepConnection = True
closeApp = False
excptnCnt = 0
while keepConnection:
    try:
        # Receive the data
        waited4Msg = time()
        LogLineLeft("Receive data")
        rcvd = servConn.recv(1024)  # receive the data
        rcvd = rcvd.decode('utf-8')
        print("ok")
        LogLineLeftRight("Received: ", rcvd)

        LogLineLeftRight("Waited for Receive:", f"{(time() - waited4Msg):.3f} s")

        # Split the data such that you separate the command
        # from the rest of the data
        dataMessage = rcvd.split(' ')
        cmd = dataMessage[0]
        payload = dataMessage[1:]

        ####### Capture (most used) #######
        # print(cmd)
        if cmd == 'CAP:SEQFET':
            reply = CaptureShutterspeedSequence(Prefix=payload[0], StorePath=imFolderPath, SS=payload[1], nPics=payload[2], tMax=payload[3], SaveSSLog=payload[4])
        elif cmd == "SRV:ARCHV":
            reply = Server_Archive(archiveFolderPath=payload[0], archiveFName=payload[1], compress=DecodeBoolStr(payload[2]), multicore=DecodeBoolStr(payload[3]), suppressParents=DecodeBoolStr(payload[4]))

        ####### Camera Conf #######
        elif cmd == "CAM:CONF:SS":                                          # ShutterSpeed (SS)
            reply = ConfShutterspeed(payload[0])
        elif cmd == "CAM:CONF:FR":                                          # FrameRate (FR)
            reply = ConfFramerate(payload[0])
        elif cmd == "CAM:CONF:AG":                                          # AnalogGain
            reply = ConfAnalogGain(payload[0])                              
        elif cmd == "CAM:CONF:AWB":                                         # AutoWhiteBalance
            reply = ConfWhiteBalance(payload[0])
        elif cmd == "CAM:CONF:SCLCRP":                                      # SCaLerCRoP (Camera-Internal precrop of the image!)
            reply = ConfScalerCrop(payload[0], payload[1])

        ####### Server Image Commands #######
        elif cmd == "SRV:IMG:BCLP":                                         # Clip of bayer-data by server
            reply = Server_ClipWinBayerImage(payload[0])
        elif cmd == "SRV:IMG:DBAY":                                         # Do a debayer of the image
            reply = Server_DemosaicClippedBayerImgs(payload[0])
        elif cmd == "SRV:IMG:SRNK":                                         # Shrink size by half after debayer
            reply = Server_ShrinkHalfDemosaicedIterations(payload[0])

        ####### Server Common Commands #######
        elif cmd == "IDN?":
            reply = IDN()
        elif cmd == "SRV:ECHO":
            reply = ECHO(payload)
        elif cmd == "SRV:PATH:RDDIR?":
            reply = mntPnt_RAMDisk
        elif cmd == "SRV:PATH:SDDIR?":
            reply = SDCardPath
        elif cmd == "SRV:PATH:IMDIR?":
            reply = imFolderPath
        elif cmd == "SRV:CLOSE":
            keepConnection = False
            closeApp = True
            reply = ackStr
        else:
            reply = 'Unknown Command'
        ####### Command Tree finished #######

        # Response
        servConn.sendall(str.encode(reply))
        LogLineLeftRight("Sent response", reply)
    except Exception as e:
        LogLineLeftRight("Exception occured:", e)
        excptnCnt += 1
        if excptnCnt > 3:  # 3 attemps ok!
            keepConnection = False
        continue
# conn.close()
LogLineLeftRight("Closed connection", "ok")


if logger != None:
    LogLineLeft("Flushing logger")
    logger.close() # Flush last log-lines and dispose
    print("ok")

print("Closing app. Bye...")