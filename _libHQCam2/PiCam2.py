from time import time, sleep
from picamera2 import Picamera2, Preview
from picamera2.controls import Controls
from _libHQCam2.Logger import LogLineLeft, LogLineLeftRight


class PiCam2:
    __IDN__ = "PiCam2"
    __cam2__ = None

    def __init__(self, fr:float=10.0, awaitWarmup:float=1.0):
        ### NOTE - Difference "configurations" and "controls" ###
        # Configurations can only be changed when the camera is in "stop"
        # Controls can be changed during runtime!
        # -> Some controls will not be changed, and therefore set up with the configuration, so that they are "static"!

        # Cam-Tuning files can be found under /usr/share/libcamera/ipa/rpi/vc4/
        LogLineLeft("Grabbing tune-file")
        _tune2 = Picamera2.load_tuning_file("imx477_scientific.json")

        # Disable gamma in tuning-contents 
        _tune2 = self.__AdjustGamma__(tune=_tune2)

        # Adjusting ExposureMode "normal" in tuning-contents (set up finer SS-list and all gains = 1 to represent a const)
        _tune2 = self.__AdjustExposureModeNormal__(tune=_tune2)

        # Adjusting MeteringMode for AGC
        _tune2 = self.__AdjustMeteringMode__(tune=_tune2)
        print("ok")


        print("Initializing and starting picamera2...")
        _fd = int(1e6 / fr)

        # Create the device using the tune-file
        self.__cam2__ = Picamera2(tuning=_tune2)
        LogLineLeftRight("Instanciating picamera2-object:", "ok")

        # Start internal camera-capture stream (no screen-output) -> Noted, this is not necessary!
        # self.__cam2__.start_preview(Preview.NULL)
        # LogLineLeftRight("Setting up NULL-preview:", "ok")

        # Create static camera-configuration with fix configs and controls! -> See description below def __init__
        self._pConf2 = self.__cam2__.create_preview_configuration(raw={"size": self.__cam2__.sensor_resolution,
                                                                         },
                                                             controls={"AnalogueGain":      1.0,
                                                                     "FrameDurationLimits": (_fd, _fd),
                                                                     }
                                                            ) 
        LogLineLeftRight("Created preview-configuration:", "ok")
        self.__cam2__.configure(self._pConf2)
        LogLineLeftRight("Preview-configuration:", "ok")

        # Start the stream
        self.__cam2__.start()
        LogLineLeftRight("Camera-start:", "ok")

        # Test from controls_3.py
        # self.__ctrls__ = Controls(self.__cam2__)
        self.__cam2__.set_controls({
            "AeEnable"            : True            ,       # Allow AutoAdjustment of ExposureTime and AGain
                                                            #  (see customized "shutter" and "gain" values above for "normal" mode, which is default)
            # "AwbEnable"         : 0               ,       # AWB off
            # "ColourGains"       : (1.0,1.0)       ,       # Additionally fix AWB-gains to 1 for (red, blue)
            # "AeEnable"          : 0               ,       # Turn off AGC & AEC
            "AnalogueGain"        : 1.0             ,       # No Amplification
            # "Brightness"        : 0.0             ,       # No relative brightness
            # "Contrast"          : 1.0             ,       # "Normal" contrast
            "ExposureTime"        : 0               ,       # SS = Auto-SS by default
            # "Saturation"        : 0               ,       # Avoid extra saturation
            # "NoiseReductionMode": 0               ,       # No noise-reduction algorithm
            # "Sharpness"         : 0               ,       # Avoid sharpening
            # "FrameDurationLimits" : (_fd, _fd)    ,       # FrameDurationLimits are already configured as static above
            # "ScalerCrop"        : [0,0] + [0,0] #list(self.__cam2__.sensor_resolution)  # No Preclip by GPU already
        })

        # Await a bit warmup time so that the camera can do all settings before reading back the ctrls
        sleep(awaitWarmup)
        LogLineLeftRight(f"Waited {awaitWarmup:.3f}s warmup-time:", "ok")

        return




    def __AdjustGamma__(self, tune):
        gamma = Picamera2.find_tuning_algo(tune, "rpi.contrast")
        gamma["ce_enable"] = 0                                            # Normally = 0 (deactivated)
        # gamma["gamma_curve"] =  [# Linear Gamma-Curve -> Not necessary, as auto-contrast is disabled (ce_enabled=0)
        #                             0,     0,
        #                          1024,  1024,
        #                          2048,  2048,
        #                          3072,  3072,
        #                          4096,  4096,
        #                          5120,  5120,
        #                          6144,  6144,
        #                          7168,  7168,
        #                          8192,  8192,
        #                          9216,  9216,
        #                         10240, 10240,
        #                         11264, 11264,
        #                         12288, 12288,
        #                         13312, 13312,
        #                         14336, 14336,
        #                         15360, 15360,
        #                         16384, 16384,
        #                         18432, 18432,
        #                         20480, 20480,
        #                         22528, 22528,
        #                         24576, 24576,
        #                         26624, 26624,
        #                         28672, 28672,
        #                         30720, 30720,
        #                         32768, 32768,
        #                         36864, 36864,
        #                         40960, 40960,
        #                         45056, 45056,
        #                         49152, 49152,
        #                         53248, 53248,
        #                         57344, 57344,
        #                         61440, 61440,
        #                         65535, 65535,
        #                     ]
        return tune
    

    def __AdjustExposureModeNormal__(self, tune): # See _libHQCam2/Extended exposure_mode normal.xlsx
        _agc = Picamera2.find_tuning_algo(tune, "rpi.agc")
        _agc["exposure_modes"]["normal"]["shutter"]  = [  100,   333,   666,  1000,  3333,  6666, 10000, 33333, 66666, 100000]
        _agc["exposure_modes"]["normal"]["gain"]     = [1.000, 1.000, 1.000, 1.000, 1.000, 1.000, 1.000, 1.000, 1.000,  1.000]

        tune = self.__AdjustMeteringMode__(tune=tune)
        tune = self.__AdjustContraintMode__(tune=tune)
        return tune


    def __AdjustMeteringMode__(self, tune):
        _agc = Picamera2.find_tuning_algo(tune, "rpi.agc")
        _agc["metering_modes"]["centre-weighted"]["weights"] = [1.0] * 15
        _agc["metering_modes"]["spot"]           ["weights"] = [1.0] * 15
        _agc["metering_modes"]["matrix"]         ["weights"] = [1.0] * 15
        return tune

    def __AdjustContraintMode__(self, tune):
        _agc = Picamera2.find_tuning_algo(tune, "rpi.agc")
        _constraints = [
            {   "bound": "LOWER",
                "q_lo": 0.98,
                "q_hi": 1.00,
                "y_target": [0, 0.2, 1000, 0.2]
            },
            {   "bound": "UPPER",
                "q_lo": 0.98,
                "q_hi": 1.00,
                "y_target": [0, 0.8, 1000, 0.8]
            },
        ]
        _agc["constraint_modes"]["normal"]    = _constraints.copy()
        _agc["constraint_modes"]["highlight"] = _constraints.copy()
        _agc["constraint_modes"]["shadows"]   = _constraints.copy()
        return tune


    def IDN(self):
        return self.__IDN__


    def CaptureMeta(self):
        return self.__cam2__.capture_metadata()


    def CaptureFromStream(self, stream="raw"):
        return self.__cam2__.capture_array(stream)


    def CaptureMetaAndImgFromStream(self, stream="raw"):
        return self.__cam2__.capture_arrays_and_metadata_(stream)


    def GetCamera(self):
        return self.__cam2__




    def SetSS(self, ss:int, Lo=0.95, Hi=1.05):
        self.__cam2__.set_controls({"AeEnable": (True, False)[ss > 0],
                                    "ExposureTime": ss,
                                    })
        return 0

    def GetSS(self):
        _param = self.__cam2__.capture_metadata()["ExposureTime"]
        return _param




    def SetScalerCrop(self, ScalerCropWin=[0,0,4056,3040]):
        self.__cam2__.set_controls({"ScalerCrop": ScalerCropWin})
        return 0

    def GetScalerCrop(self):
        param = self.__cam2__.capture_metadata()["ScalerCrop"]
        param = list(param)
        return param




    def SetAG(self, ag:float=1.0):
        _param = {"AnalogueGain": ag}
        self.__cam2__.set_controls(_param)
        return 0

    def GetAG(self):
        _param = self.__cam2__.capture_metadata()["AnalogueGain"]
        return _param




    def SetAWB(self, awb:tuple=(1.0,1.0)):
        _param = {"ColourGains": awb}
        self.__cam2__.set_controls(_param)
        return 0

    def GetAWB(self):
        _param = self.__cam2__.capture_metadata()["ColourGains"]
        return _param




    def __SetFD__(self, fd:int):
        fd = int(fd)
        self._pConf2['controls']['FrameDurationLimits'] = (fd, fd)
        self.__cam2__.configure(self._pConf2)
        return 0

    def SetFD(self, fd:int=100000):
        self.__cam2__.stop()
        self.__SetFD__(fd)
        self.__cam2__.start()
        return 0

    def GetFD(self):
        _param = self.__cam2__.capture_metadata()["FrameDuration"]
        return _param




    def SetFR(self, fr:float=10.0):
        _fd = 1e6 / fr
        self.SetFD(_fd)
        return 0

    def GetFR(self):
        param = 1e6 / self.GetFD()
        return param

