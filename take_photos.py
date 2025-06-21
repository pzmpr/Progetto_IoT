import cv2 as cv
from time import time

# Initialize webcam
cam = cv.VideoCapture(0)

# Capture one frame every 5 seconds
previous = time()
x = 1
delta = 0
while True:
    current = time()
    delta += current - previous
    previous = current

    if delta > 5:
        ret, frame = cam.read()
        dest = "Images/captured_image" + str(x) + ".png"
        x = x + 1
        cv.imwrite(dest, frame)
        delta = 0
        cam.grab()
        cam.grab()
        cam.grab()
        cam.grab()
        cam.grab()
    if x > 5:
        break

cam.release()