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

date = str(datetime.date.today())
dest = "Videos/rec-" + date + ".avi"
fourcc = cv.VideoWriter_fourcc(*'DIVX')
out = cv.VideoWriter(dest, fourcc, 20, (640,  480))

output_frame = None
lock = threading.Lock()
app = Flask(__name__)

host = "127.0.0.1"
port = 1883
topic = "Video"

prev_frame = None
frame = None  # empty variable to store latest message received

# signal handler
stop = False

def handle_signal(signum, frame):
    global stop, app
    stop = True
    print("\nExiting...")

signal.signal(signal.SIGINT, handle_signal)

# connessione al database
conn = psycopg2.connect(
    dbname="Iot",
    user="postgres",
    password="vivamilan04",
    host="127.0.0.1",
    port="5432"
)
cur = conn.cursor()
print("Connected to database Iot")

def subscribe():
    global mqttc, stop, dest, date
    while not stop:
        mqttc.loop() # Start networking daemon
    cv.destroyAllWindows()
    update_db_Registrazioni(date)
    compress_video(dest, date)
    os.remove(dest)
    print("Video compresso")
    
def on_connect(client, userdata, flags, reason_code, properties):  # The callback for when the client connects to the broker
    global topic
    client.subscribe(topic)  # Subscribe to the topic, receive any messages published on it
    print("Subscring to topic :", topic)

def on_message(client, userdata, msg):  # The callback for when a PUBLISH message is received from the server.
    global out, frame, prev_frame, lock, output_frame
    nparr = np.frombuffer(msg.payload, np.uint8)
    frame = cv.imdecode(nparr,  cv.IMREAD_COLOR)
    with lock:
        output_frame = frame.copy()
    out.write(frame)
    cv.imshow('recv', frame)
    if cv.waitKey(1) & 0xFF == ord('q'):
        return

def update_db_Registrazioni(data):
    nome = "rec-" + data
    cur.execute("""
                INSERT INTO "Registrazioni"(rec_nome)
                VALUES (%s)
                ON CONFLICT DO NOTHING
                """, (nome,))
    conn.commit()
    print(f"[✓] Video registrato nel database")

def compress_video(dest, date):
    print("Compressione video...")
    result = ffmpeg.input(dest)
    result = ffmpeg.output(result, "Videos/rec-"+date+".mp4", bitrate='800k', loglevel='quiet')
    ffmpeg.run(result, overwrite_output = True)

def generate():
    global output_frame, lock
    # loop over frames from the output stream
    while True:
        # wait until the lock is acquired
        with lock:
            # check if the output frame is available, otherwise skip
            # the iteration of the loop
            if output_frame is None:
                time.sleep(0.1)
                continue
            # encode the frame in JPEG formatpietrozmpr@gmail.com
            (flag, encodedImage) = cv.imencode(".jpg", output_frame)
            # ensure the frame was successfully encoded
            if not flag:
                continue
        # yield the output frame in the byte format
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
mqttc.on_connect = on_connect  # Define callback function for successful connection
mqttc.message_callback_add(topic, on_message)
mqttc.connect(host,port)  # connecting to the broking server

t = threading.Thread(target=subscribe)    # make a thread to loop for subscribing
t.start() # run this thread

app.run(host="0.0.0.0", port=8000, debug=True,
        threaded=True, use_reloader=False)