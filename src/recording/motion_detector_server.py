import cv2 as cv
import threading
import paho.mqtt.client as mqtt
import argparse
import time
import datetime
import signal
import imutils
import time
import os
import ffmpeg
import numpy as np
import psycopg2
from flask import Flask, Response, render_template

# Variabili per tempo e percorso file
date = str(datetime.date.today())
dest = "Videos/rec-" + date + ".avi"

# Variabili per stream video
fourcc = cv.VideoWriter_fourcc(*'DIVX')
out = cv.VideoWriter(dest, fourcc, 20, (640,  480))
prev_frame = None
frame = None
output_frame = None

# Variabili per thread e connessione pagina web
lock = threading.Lock()
app = Flask(__name__)

# Variabili connessione mqtt
host = "127.0.0.1"
port = 1883
topic = "Video"
qos = 2

# signal handler
stop = False

def handle_signal(signum, frame):
    global stop, app
    stop = True
    print("\nUscita...")

signal.signal(signal.SIGINT, handle_signal)

# connessione al database
conn = psycopg2.connect(
    dbname = "Iot",
    user = "postgres",
    password = "",
    host = host,
    port = "5432"
)
cur = conn.cursor()
print("Connesso al database Iot")
    
def on_connect(client, userdata, flags, reason_code, properties):
    global topic, qos
    client.subscribe(topic, qos)

def on_message(client, userdata, msg):
    global out, frame, prev_frame, lock, output_frame
    nparr = np.frombuffer(msg.payload, np.uint8)
    frame = cv.imdecode(nparr,  cv.IMREAD_COLOR)
    with lock:
        output_frame = frame.copy()
    out.write(frame)
    # cv.imshow('recv', frame)              # mostra stream a schermo
    # if cv.waitKey(1) & 0xFF == ord('q'):
    #    return

def subscribe():
    global mqttc, stop, dest, date
    while not stop:
        mqttc.loop()
    cv.destroyAllWindows()
    update_db_Registrazioni(date)
    # chiusura connessione database
    cur.close()
    conn.close()
    compress_video(dest, date)
    os.remove(dest)
    print("Video compresso")

def update_db_Registrazioni(data):
    nome = "rec-" + data
    cur.execute("""
                INSERT INTO "Registrazioni"(rec_nome)
                VALUES (%s)
                ON CONFLICT DO NOTHING
                """, (nome,))
    conn.commit()
    print("Video registrato nel database")

# compressione del video
# si attiva quando il flusso di frame e' terminato (dopo CTRL-C)
def compress_video(dest, date):
    print("Compressione video...")
    result = ffmpeg.input(dest)
    result = ffmpeg.output(result, "Videos/rec-"+date+".mp4", bitrate='800k', loglevel='quiet')
    ffmpeg.run(result, overwrite_output = True)

# genera i frame per lo stream nella pagina web
def generate():
    global output_frame, lock
    while True:
        with lock:
            if output_frame is None:
                # time.sleep(0.1)
                continue
            # codifica il frame in formatp JPEG
            (flag, encodedImage) = cv.imencode(".jpg", output_frame)
            # assicura che il frame sia stato codificato
            if not flag:
                continue
        # restituisci l'immagine come array di byte
        yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + 
            bytearray(encodedImage) + b'\r\n')



@app.route('/')
def index():
    return render_template("index.html")

@app.route("/video_feed")
def video_feed():
    return Response(generate(),
        mimetype = "multipart/x-mixed-replace; boundary=frame")

mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_connect = on_connect  # callback function
mqttc.message_callback_add(topic, on_message)
mqttc.connect(host,port)  # connessione broker

t = threading.Thread(target=subscribe) # thread per subscribe
t.start()

app.run(host="0.0.0.0", port=8000, debug=True,
        threaded=True, use_reloader=False)