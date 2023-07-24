import os
from os.path import join
from subprocess import call
import time


def CreateFolder4User(folderPath, user:str="pi", group:str="pi"):
    if(not os.path.isdir(folderPath)):
        os.system(f"sudo mkdir -p {folderPath}")
        os.system(f"sudo chown {user}:{group} {folderPath}")


class RAMDisk:
    __mntPnt__ = ""
    __user__ = ""
    __group__ = ""
    __mounted__ = False

    def __init__(self, mntPnt:str, mbSize:int=4096, user:str="pi", group:str="pi"):
        self.__mntPnt__ = mntPnt
        self.__user__ = user
        self.__group__ = group

        try:
            # make sure that the directory is present on the RPi sudo mkdir: /mnt/ramdisk
            if(not os.path.isdir(mntPnt)):
                os.system(f"sudo mkdir -p {mntPnt}")
                os.system(f"sudo chown {user}:{group} {mntPnt}")

            # Unmount old mounts on /media/ramdisk when not in use! (otherwise it blocks)
            while (call(f"mount | grep \"{mntPnt}\"", shell=True) == 0):
                call(f"sudo umount \"{mntPnt}\"", shell=True)
                time.sleep(0.5) # Short wait to save some CPU-usage

            call(f"sudo mount -t tmpfs -o size={mbSize}M tmpfs \"{mntPnt}\"", shell=True)
            self.__mounted__ = True
        except Exception as e:
            self.__mntPnt__ = ""
            self.__mounted__ = False




    def Close(self, unmount=False):
        if unmount:
            self.UnmountAwait()




    def IsMounted(self):
        return self.__mounted__




    def Unmount(self):
        call(f"sudo umount \"{self.__mntPnt__}\"", shell=True)
        self.__mounted__ = False
    
    def IsInUse(self):
        isBusy = call(f"mount | grep \"{self.__mntPnt__}\"", shell=True) == 0
        return isBusy

    def UnmountAwait(self):
        # Unmount old mounts on /media/ramdisk when not in use! (otherwise it blocks)
        while (self.IsInUse()):
            self.Unmount()
            time.sleep(0.5) # Short wait to save some CPU-usage

