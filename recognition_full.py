import cv2 as cv
from time import time
import face_recognition
import os

# Initialize webcam
cam = cv.VideoCapture(0)

# Initialize images variables
known_image = face_recognition.load_image_file("Images/pietro.jpg")
known_encoding = face_recognition.face_encodings(known_image)[0]

# Capture one frame every 5 seconds
previous = time()
x = 1
delta = 0
while True:
    current = time()
    delta += current - previous
    previous = current

    if delta > 3:
        ret, frame = cam.read()
        dest = "Images/captured_image" + str(x) + ".png"
        cv.imwrite(dest, frame)

        # creazione dati immagine sconosciuta
        unknown_image = face_recognition.load_image_file(dest)
        # non sono stati riconosciuti volti nell'immagine
        if(len(face_recognition.face_encodings(unknown_image)) == 0 ):
            print("L'immagine sconosciuta e' quella di una persona conosciuta: No")
            try: 
                os.remove(dest)
            except: pass
        # ci sono volti nell'immagine
        else:
            unknown_encoding = face_recognition.face_encodings(unknown_image)[0]
            #creazione risposta
            results = face_recognition.compare_faces([known_encoding], unknown_encoding)
            answer = "Si" if results[0] else "No"
            print("L'immagine sconosciuta e' quella di una persona conosciuta:", answer)
            try: 
                os.remove(dest)
            except: pass
        x = x + 1
        delta = 0
        # elimino foto nel buffer
        cam.grab()
        cam.grab()
        cam.grab()
        cam.grab()
        cam.grab()
    if x > 5:
        break

cam.release()