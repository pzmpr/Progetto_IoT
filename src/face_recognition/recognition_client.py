import cv2 as cv
from time import time
from datetime import datetime
import os
import signal
import paho.mqtt.client as mqtt
import sys

# Inizializzazione webcam
cam = cv.VideoCapture(0)

# Variabili per intervallo di tempo o percorso file
previous = time()
delta = 0
dest = None

# Variabili connessione mqtt
qos  = 2
host = "127.0.0.1"
port = 1883
sub_topic1 = "Images/Results/answer"
sub_topic2 = "Images/Results/name"
pub_topic  = "Images/content"
recieved_ans = False
recieved_nm  = False
results = ""
name    = ""

# signal handler
stop = False

def handle_signal(signum, frame):
    global stop
    stop = True
    print("\nUscita...")

signal.signal(signal.SIGINT, handle_signal)

def remove_file(dest):
    try:
        os.remove(dest)
    except: pass

def on_publish(client, userdata, mid, reason_code, properties):
    print('Foto inviata (%d)' %mid)
    
def on_message(client, userdata, message):
    global results, name, recieved_ans, recieved_nm, sub_topic1, sub_topic2
    if message.topic == sub_topic1:
        results = str(message.payload.decode("utf-8"))
        recieved_ans = True
    if message.topic == sub_topic2:
        name = str(message.payload.decode("utf-8"))
        recieved_nm = True
    
def on_connect(client, userdata, flags, reason_code, properties):
    global sub_topic, qos
    if reason_code.is_failure:
        print(f"\nImpossibile connettersi al broker: {reason_code}.")
    else:
        client.subscribe(sub_topic1, qos)
        client.subscribe(sub_topic2, qos)

def print_results():
    global recieved_ans, recieved_nm, results, name, dest
    recieved_ans = False
    recieved_nm = False
    if results == "NA":
        print("Non e' stato riconosciuto alcun volto")
    elif results == "Si":
        answer = "Si, e\' " + name
        print("L'immagine sconosciuta e' quella di una persona conosciuta:", answer)
    elif results == "No":
        answer = "No"
        print("L'immagine sconosciuta e' quella di una persona conosciuta:", answer)



mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_connect = on_connect
mqttc.on_publish = on_publish
mqttc.on_message = on_message

mqttc.connect(host, port)
mqttc.loop_start()
while not stop: 
    current = time()
    delta += current - previous
    previous = current

    # cattura un frame ogni 5 secondi
    if delta > 5:
        ret, frame = cam.read()
        dest = "foto/captured_image.png"
        cv.imwrite(dest, frame)

        # invio immagine a server
        img = open(dest, "rb")
        fileContent = img.read()
        byteArr = bytearray(fileContent)
        mqttc.publish(pub_topic, byteArr)
        img.close()
        
        if recieved_ans and recieved_nm:
            print_results()

        delta = 0
        # elimino foto nel buffer (la fotocamera scatta foto in successione)
        cam.grab()
        cam.grab()
        cam.grab()
        cam.grab()
        cam.grab()
    remove_file(dest)

mqttc.loop_stop()
cam.release()
