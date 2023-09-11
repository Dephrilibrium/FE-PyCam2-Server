from time import sleep

print("Starting standard JPGs")
import CalibrationLightStandardJPG

wTime = 3
print(f"Standard-JPGs done. Waiting for {wTime:.2f}s")
sleep(wTime)

print("Starting standard PNGs")
import CalibrationLightLinearPNG

print("End of Queue")