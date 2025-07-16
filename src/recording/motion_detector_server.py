import cv2 as cv
import threading
import paho.mqtt.client as mqtt
import argparse
import datetime
import signal
import imutils
import time
import os
import ffmpeg
import numpy as np

dest = "Videos/rec-" + str(datetime.date.today()) + ".avi"
fourcc = cv.VideoWriter_fourcc(*'DIVX')
out = cv.VideoWriter(dest, fourcc, 12.0, (640,  480))

host = "127.0.0.1"
port = 1883
topic = "Video"

prev_frame = None
frame = None  # empty variable to store latest message received

# signal handler
stop = False

def handle_signal(signum, frame):
    global stop
    stop = True
    print("\nExiting...")

signal.signal(signal.SIGINT, handle_signal)

def subscribe():
    global mqttc, stop
    while not stop:
        mqttc.loop() # Start networking daemon
    cv.destroyAllWindows()
    
    
def on_connect(client, userdata, flags, reason_code, properties):  # The callback for when the client connects to the broker
    global topic
    client.subscribe(topic)  # Subscribe to the topic, receive any messages published on it
    print("Subscring to topic :", topic)

def on_message(client, userdata, msg):  # The callback for when a PUBLISH message is received from the server.
    global out, frame, prev_frame
    nparr = np.frombuffer(msg.payload, np.uint8)
    frame = cv.imdecode(nparr,  cv.IMREAD_COLOR)
    # TODO codice compressione video
    out.write(frame)
    cv.imshow('recv', frame)
    # TODO caricare nel db dati registrazione
    if cv.waitKey(1) & 0xFF == ord('q'):
        return

mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_connect = on_connect  # Define callback function for successful connection
mqttc.message_callback_add(topic, on_message)
mqttc.connect(host,port)  # connecting to the broking server

t = threading.Thread(target=subscribe())    # make a thread to loop for subscribing
t.start() # run this thread
