import cv2 as cv
import threading
import paho.mqtt.client as mqtt
import datetime
import signal
import imutils
import os

TIMER_VALUE  = 100  # circa 5 secondi
MINIMUM_AREA = 500  # area minima bounding box
TOLERANCE    = 50   # tolleranza rilevamento di movimento

# Variabili connessione mqtt
mqtt_host = "localhost"
port  = 1883
topic = "Videos"
flag_is_connected = False

# Variabili per stream video e rilevamento di movimento
prev_frame = None
frame      = None
active     = False
text       = "Libero"
timer      = TIMER_VALUE

# signal handler
stop = False

def handle_signal(signum, frame):
    global stop, flag_is_connected
    stop = True
    print("\nUscita...")
    if flag_is_connected:
        mqttc.unsubscribe(topic)
        mqttc.disconnect()

signal.signal(signal.SIGINT, handle_signal)

def on_connect(client, userdata, flags, reason_code, properties):
    global flag_is_connected
    if reason_code.is_failure:
        print(f"\nImpossibile connettersi al broker: {reason_code}.")
    else:
        print("Connesso al broker mqtt")
        flag_is_connected = True

def modify_frame():
    global frame, prev_frame, text
    text = "Libero"
    # scala il frame, convertilo a scala di grigi, sfuoca
    frame = cv.resize(frame, (640,480))
    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    gray = cv.GaussianBlur(gray, (21, 21), 0)
    # se il primo frame e' None, inizializzalo
    if prev_frame is None:
        prev_frame = gray
    
    # calcola il valore assoluto della differenza tra il frame attuale e quello precedente
    frame_delta = cv.absdiff(prev_frame, gray)
    # aggiorna il frame precedente con l'ultimo frame
    prev_frame = gray

    # calcola zone con movimento rilevato
    thresh = cv.threshold(frame_delta, TOLERANCE, 255, cv.THRESH_BINARY)[1]
    # dilata l'immagine soglia per riempire i buchi, poi trova i contorni nell'immagine soglia
    thresh = cv.dilate(thresh, None, iterations = 2)
    cnts = cv.findContours(thresh.copy(), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)  
    # cicla sui contorni
    for c in cnts:
        # se il contorno e' troppo piccolo, ignoralo
        if cv.contourArea(c) < MINIMUM_AREA:
            continue
        # calcola la bounding box per il contorno, disegnala sul frame, aggiorna il testo
        (x, y, w, h) = cv.boundingRect(c)
        cv.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        text = "Occupato"
    
    # scrittura stato della stanza e timestamp
    cv.putText(frame, "Stato: {}".format(text), (10, 20),
        cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
    cv.putText(frame, datetime.datetime.now().strftime("%a %d %B %Y %H:%M:%S"),
        (10, frame.shape[0] - 10), cv.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)

def stream():
    global frame, active, timer, text, mqttc, topic
    print("Streaming avviato")
    while not stop:
        _ , frame = cam.read()
        # se non c'e' alcun frame, lo stream e' finito
        if frame is None:
            return
        modify_frame()
        if text == "Occupato":
            active = True
            timer = TIMER_VALUE
            frame_str = cv.imencode('.jpg', frame)[1].tobytes()
            mqttc.publish(topic, frame_str)
        elif active:
            frame_str = cv.imencode('.jpg', frame)[1].tobytes()
            mqttc.publish(topic, frame_str)
            timer -= 1
            if timer == 0:
                active = False
                timer = TIMER_VALUE



mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_connect = on_connect

mqttc.connect(mqtt_host, port)
cam = cv.VideoCapture(0)
streaming_thread = threading.Thread(target=stream)
streaming_thread.start()
mqttc.loop_forever()

# chiusura telecamera
cam.release()
