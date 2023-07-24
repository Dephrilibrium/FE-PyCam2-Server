import time



def duration(start):
    return time.time() - start

def how_long(start, msg):
    d = duration(start)
    print(str.format("{} took {:.3f}s", msg, d))
    return d


def ConvertFractional(frac):
    return frac.numerator / frac.denominator


def capture_Intervall(duration, start):
    cur = time.time()-start
    if cur > 0 and cur < duration:
        time.sleep(duration-cur)
    elif (cur != 0):
        print('Capture took longer than Intervall time!!')
    

__booleanInputTrue__ = ["1",  "true",  "on", "yes", "y"]
__booleanInputFalse__ = ["0", "false", "off",  "no", "n"]
def DecodeBoolStr(boolStr:str):
    global __booleanInputTrue__, __booleanInputFalse__
    boolStr = boolStr.lower()
    if any([boolStr == bCmp for bCmp in __booleanInputTrue__]):
        return True
    # if any([boolStr == bCmp for bCmp in __booleanInputFalse__]):
    #     return True

    # raise Exception(f"Unsupported input - Needs to be {__booleanInputTrue__} for True or {__booleanInputFalse__} for False")
    return False # Default False!    
