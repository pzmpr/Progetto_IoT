import cv2 as cv
import threading
import paho.mqtt.client as mqtt
import datetime
import signal
import imutils
import os
import ffmpeg
import numpy as np
import psycopg2
from flask import Flask, Response, render_template

FPS = 10  # frame/sec del video
RESOLUTION = (640, 480)  # risoluzione video

# Variabili per tempo e percorso file
date = str(datetime.date.today())
dest = "Videos/rec-" + date + ".avi"

# Variabili per stream video
if not os.path.exists("Videos"):
    os.makedirs("Videos")
fourcc       = cv.VideoWriter_fourcc(*'DIVX')
out          = cv.VideoWriter(dest, fourcc, FPS, RESOLUTION)
prev_frame   = None
frame        = None
output_frame = None

# Variabili per thread e connessione pagina web
lock = threading.Lock()
app  = Flask(__name__)

# Variabili connessione mqtt
mqtt_host = "localhost"
db_host   = "localhost"
port  = 1883
topic = "Videos"
qos   = 0
flag_is_connected = False

# signal handler
def handle_signal(signum, frame):
    global app, flag_is_connected, dest, date
    print("\nUscita...")
    if flag_is_connected:
        mqttc.unsubscribe(topic)
        mqttc.disconnect()
        cv.destroyAllWindows()
        # controlla che il file non sia vuoto
        if os.path.getsize(dest) != 0:
            update_db_Registrazioni(date)
            compress_video(dest, date)
        remove_file(dest)
    # chiusura connessione database
    cur.close()
    conn.close()
    os._exit(0)

signal.signal(signal.SIGINT, handle_signal)

def remove_file(dest):
    try:
        os.remove(dest)
    except: pass

# connessione al database
conn = psycopg2.connect(
    dbname   = "Iot",
    user     = "postgres",
    password = "",
    host     = db_host,
    port     = "5432"
)
cur = conn.cursor()
print("Connesso al database Iot")
    
def on_connect(client, userdata, flags, reason_code, properties):
    global topic, qos, flag_is_connected
    if reason_code.is_failure:
        print(f"\nImpossibile connettersi al broker: {reason_code}.")
    else:
        print("Connesso al broker mqtt")
        client.subscribe(topic, qos)
        flag_is_connected = True

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

def update_db_Registrazioni(data):
    cur.execute("""
                INSERT INTO "Registrazioni"(data)
                VALUES (%s)
                ON CONFLICT DO NOTHING
                """, (data,))
    conn.commit()
    print("Video registrato nel database")

# compressione del video
# si attiva quando il flusso di frame e' terminato (dopo CTRL-C)
def compress_video(dest, date):
    print("Compressione video...")
    result = ffmpeg.input(dest)
    dest = "Videos/rec-"+date
    i = 1
    if os.path.exists(dest+".mp4"):
        while os.path.exists(f"{dest}({i}).mp4"):
            i += 1
        dest = (f"{dest}({i})")
    dest = dest + ".mp4"
    result = ffmpeg.output(result, dest, bitrate='800k', loglevel='error')
    try:
        ffmpeg.run(result, overwrite_output = True, capture_stderr = True)
    except ffmpeg.Error as e:
        err = e.stderr.decode('utf-8') if e.stderr else "None"
        print("Compressione fallita: ", err)
        return
    print("Video compresso")

# genera i frame per lo stream nella pagina web
def generate():
    global output_frame, lock
    while True:
        with lock:
            if output_frame is None:
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
mqttc.on_connect = on_connect
mqttc.on_message = on_message
mqttc.connect(mqtt_host, port)

mqttc.loop_start()
app.run(host="localhost", port=8000, debug=False,
        threaded=True, use_reloader=False)
