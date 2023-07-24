import os


# def CompressFolder(compressPath:str, tarGzFName:str, Multicore=True, SuppressParents=True):
#     compressTool = "--use-compress-program=pigz" if Multicore == True else "-z"

#     if SuppressParents:
#         retVal = os.system(f"tar {compressTool} -cf \"{tarGzFName}\" -C \"{compressPath}\" .")
#     else:
#         retVal = os.system(f"tar {compressTool} -cf \"{tarGzFName}\" \"{compressPath}\"")
    
#     return retVal


def ArchiveFolder(archivePath:str, tarFName:str, compress=True, multicore=True, suppressParents=True):
    compressTool = ""
    if compress:                                                                        # If compression is wanted
        compressTool = "--use-compress-program=pigz" if multicore == True else "-z"     #  add parameters for compression

    if suppressParents:
        retVal = os.system(f"tar {compressTool} -cf \"{tarFName}\" -C \"{archivePath}\" .")
    else:
        retVal = os.system(f"tar {compressTool} -cf \"{tarFName}\" \"{archivePath}\"")

    return retVal