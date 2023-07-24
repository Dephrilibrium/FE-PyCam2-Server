import sys




class StdOutLogger():
    def __init__(self, LogFilePath):
        """_summary_

        Args:
            LogFilePath (string): Filepath of logfile. (existing one gets overwritten)
        """
        self.terminal = sys.stdout
        self.log = open(LogFilePath, "w")
        sys.stdout = self

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        # this flush method is needed for python 3 compatibility.
        # this handles the flush command by doing nothing.
        # you might want to specify some extra behavior here.
        self.terminal.flush()
        self.log.flush()
        pass
    
    def close(self):
        self.__del__()

    def __del__(self):
        sys.stdout = self.terminal
        self.terminal = None
        # self.log.flush() # Ensure everything is written
        self.log.close() # Close file


def LogLineLeft(LeftText, LeftAlign=40):
    print(LeftText.ljust(LeftAlign), end="")

def LogLineLeftRight(LeftText, RightText, LeftAlign=40):
    LogLineLeft(LeftText, LeftAlign)
    print(RightText)
