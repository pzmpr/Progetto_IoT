from time import time
from datetime import datetime
import face_recognition
import os
import signal
import paho.mqtt.client as mqtt
import sys

# Inizializzazione variabili immagini
known_encodings_buffer = []

# Inserire percorso delle immagini note (specificando il nome della persona)
known_image = face_recognition.load_image_file("Images/ezio_greggio.jpg")
known_encoding = face_recognition.face_encodings(known_image)[0]
known_encodings_buffer += [(known_encoding, "Ezio Greggio")]

known_image = face_recognition.load_image_file("Images/alberto_angela.jpg")
known_encoding = face_recognition.face_encodings(known_image)[0]
known_encodings_buffer += [(known_encoding, "Alberto Angela")]

# Inizializzazione contatore persone, time e intervallo
count = 0
dest = "Images/captured_image.png"
presents = []

# Inizializzazione dati connessione
flag_is_connected = False
qos = 2
host = "127.0.0.1"
port = 1883
recieved = False
results = ("","")

# signal handler
stop = False

def handle_signal(signum, frame):
    global stop
    stop = True
    print("\nExiting...")

signal.signal(signal.SIGINT, handle_signal)

def on_publish(client, userdata, mid, reason_code, properties):
    print("Risposta inviata (%d)" %mid)
    
def on_message(client, userdata, message):
    global recieved
    file = open(dest, "wb")
    file.write(message.payload)
    print("Image Received")
    file.close()
    recieved = True
    
def on_connect(client, userdata, flags, reason_code, properties):
    global topic, qos
    if reason_code.is_failure:
        print(f"\nFailed to connect: {reason_code}.")
    else:
        client.subscribe("Images", qos)

def compute_and_send():
    global results, recieved, count, dest, presents
    # exited from loop, image recieved
    recieved = False
    # creazione dati immagine sconosciuta
    unknown_image = face_recognition.load_image_file(dest)
    # non sono stati riconosciuti volti nell'immagine
    if( len(face_recognition.face_encodings(unknown_image)) == 0 ):
        print("Non e' stato riconosciuto alcun volto")
        results = ("NA", "NA")
        try:
            os.remove(dest)
        except: pass
    # ci sono volti nell'immagine
    else:
        unknown_encoding = face_recognition.face_encodings(unknown_image)[0]
        # creazione risposta
        for encoding in known_encodings_buffer:
            answer = face_recognition.compare_faces([encoding[0]], unknown_encoding)
            if answer:
                name = encoding[1]
                break
        if answer[0]:
            results = ("Si", name)
            if name not in presents:
                presents += [name]
                count += 1
            # TODO carica nel db count e timestamp (ora)
        else:
            results = ("No", "")
            # TODO carica nel db dati persona sconosciuta e immagine nel file system
        print("L'immagine sconosciuta e' quella di una persona conosciuta:", results[0])
        try:
            os.remove(dest)
        except: pass

    mqttc.publish("Results/answer", results[0])
    mqttc.publish("Results/name", results[1])



mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_connect = on_connect
mqttc.on_publish = on_publish
mqttc.on_message = on_message

mqttc.connect(host, port)
mqttc.loop_start() # inizio loop
while not stop:
    if recieved:
        compute_and_send()
mqttc.loop_stop() # fine loop
