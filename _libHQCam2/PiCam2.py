from time import time, sleep
from picamera2 import Picamera2, Preview, Controls
from libcamera import controls
from _libHQCam2.Logger import LogLineLeft, LogLineLeftRight


class PiCam2:
    __IDN__ = "PiCam2"
    __cam2__ = None
    __tune2__ = None
    __pconf2__ = None
    __ctrls__ = None


    def __init__(self, fr:float=10.0, awaitWarmup:float=1.0):
        # global __cam2__, __tune2__, __pconf2__

        LogLineLeft("Grabbing tune-file")
        # Cam-Tuning can be found under /usr/share/libcamera/ipa/raspberrypi/
        self.__tune2__ = Picamera2.load_tuning_file("imx477_scientific.json")

        # # Optional settings!
        # gamma = Picamera2.find_tuning_algo(camTune, "rpi.contrast")
        # gamma["ce_enable"] = 0                                            # Normally = 0 (deactivated)
        # gamma["gamma_curve"] =  [           # Linear Gamma-Curve
        #                         0,     0,
        #                     1024,  1024,
        #                     2048,  2048,
        #                     3072,  3072,
        #                     4096,  4096,
        #                     5120,  5120,
        #                     6144,  6144,
        #                     7168,  7168,
        #                     8192,  8192,
        #                     9216,  9216,
        #                     10240, 10240,
        #                     11264, 11264,
        #                     12288, 12288,
        #                     13312, 13312,
        #                     14336, 14336,
        #                     15360, 15360,
        #                     16384, 16384,
        #                     18432, 18432,
        #                     20480, 20480,
        #                     22528, 22528,
        #                     24576, 24576,
        #                     26624, 26624,
        #                     28672, 28672,
        #                     30720, 30720,
        #                     32768, 32768,
        #                     36864, 36864,
        #                     40960, 40960,
        #                     45056, 45056,
        #                     49152, 49152,
        #                     53248, 53248,
        #                     57344, 57344,
        #                     61440, 61440,
        #                     65535, 65535,
        #                 ]
        print("ok")

        print("Initializing and starting picamera2...")
        self.__cam2__ = Picamera2(tuning=self.__tune2__)
        LogLineLeftRight("Instanciating picamera2-object:", "ok")
        self.__cam2__.start_preview(Preview.NULL)
        LogLineLeftRight("Starting NULL-preview:", "ok")

        _fd = int(1e6 / fr)
        defaultCtrls ={
                       "AwbEnable": 0,                                              # AWB off
                       "ColourGains":(1.0,1.0),                                     # Additionally fix AWB-gains to 1 for (red, blue)
                       "AeEnable": 0,                                               # Turn off AGC & AEC
                       "AnalogueGain": 1.0,                                         # No Amplification
                       "Brightness": 0.0,                                           # No relative brightness
                       "Contrast": 1.0,                                             # "Normal" contrast
                       "ExposureTime": 1000,                                        # SS
                       "Saturation": 0,                                             # Avoid extra saturation
                       "NoiseReductionMode": 0,                                     # No noise-reduction algorithm
                       "Sharpness": 0,                                              # Avoid sharpening
                       "FrameDurationLimits": (_fd, _fd),                           # Predefine FrameDuration
                       "ScalerCrop": [0,0] + [0,0] #list(self.__cam2__.sensor_resolution)  # No Preclip by GPU already
                     }
        # self.__pconf2__ = self.__cam2__.create_preview_configuration(raw={"size": self.__cam2__.sensor_resolution}, main={"format": "BGR888", "size": (64,64)}, controls=defaultCtrls)
        self.__pconf2__ = self.__cam2__.create_preview_configuration(raw={"size": self.__cam2__.sensor_resolution}, controls=defaultCtrls)
        self.__cam2__.configure(self.__pconf2__)
        self.__ctrls__ = Controls(self.__cam2__)
        LogLineLeftRight("Setting up standard-controls:", "ok")
        print("Standard-controls are:")
        print(defaultCtrls)


        self.__cam2__.start()
        LogLineLeftRight("Camera-start:", "ok")
        sleep(awaitWarmup)
        LogLineLeftRight(f"Waited {awaitWarmup:.3f}s warmup-time:", "ok")

        return




    def IDN(self):
        return self.__IDN__


    def CaptureMeta(self):
        return self.__cam2__.capture_metadata()


    def CaptureFromStream(self, stream="raw"):
        return self.__cam2__.capture_array("raw")


    def CaptureMetaAndImgFromStream(self, stream="raw"):
        return self.__cam2__.capture_arrays_and_metadata_(stream)


    def GetCamera(self):
        return self.__cam2__




    def SetSS(self, ss:int, Lo=0.95, Hi=1.05):
        # global __cam2__
        # _param = {"ExposureTime": ss}
        # self.__cam2__.set_controls(_param)
        self.__ctrls__.ExposureTime = ss
        self.__cam2__.set_controls(self.__ctrls__)
        return 0

    def GetSS(self):
        _param = self.__cam2__.capture_metadata()["ExposureTime"]
        # _param = self.__ctrls__.ExposureTime
        return _param




    def SetScalerCrop(self, ScalerCropWin=[0,0,4056,3040]):
        # global __cam2__
        self.__cam2__.set_controls({"ScalerCrop": ScalerCropWin})
        return 0

    def GetScalerCrop(self):
        # global __cam2__
        param = self.__cam2__.capture_metadata()["ScalerCrop"]
        param = list(param)
        return param




    def SetAG(self, ag:float=1.0):
        # global __cam2__
        _param = {"AnalogueGain": ag}
        self.__cam2__.set_controls(_param)
        return 0

    def GetAG(self):
        # global __cam2__
        _param = self.__cam2__.capture_metadata()["AnalogueGain"]
        return _param




    def SetAWB(self, awb:tuple=(1.0,1.0)):
        # global __cam2__
        _param = {"ColourGains": awb}
        self.__cam2__.set_controls(_param)
        return 0

    def GetAWB(self):
        # global __cam2__
        _param = self.__cam2__.capture_metadata()["ColourGains"]
        return _param




    def __SetFD__(self, fd:int):
        # global __cam2__, __pconf2__
        fd = int(fd)
        self.__pconf2__['controls']['FrameDurationLimits'] = (fd, fd)
        self.__cam2__.configure(self.__pconf2__)
        return 0

    def SetFD(self, fd:int=100000):
        # global __cam2__
        self.__cam2__.stop()
        self.__SetFD__(fd)
        self.__cam2__.start()
        return 0

    def GetFD(self):
        # global __cam2__
        _param = self.__cam2__.capture_metadata()["FrameDuration"]
        return _param




    def SetFR(self, fr:float=10.0):
        # global __cam2__
        _fd = 1e6 / fr
        self.SetFD(_fd)
        return 0

    def GetFR(self):
        param = 1e6 / self.GetFD()
        return param

