from time import time
import datetime
import os
import signal
import paho.mqtt.client as mqtt
import sys
import psycopg2
import face_recognition

# Inizializzazione variabili immagini
known_encodings_buffer = []

# Inserire percorso delle immagini note (specificando il nome della persona)
known_image = face_recognition.load_image_file("Images/ezio_greggio.jpg")
known_encoding = face_recognition.face_encodings(known_image)[0]
known_encodings_buffer += [(known_encoding, "Ezio Greggio", "1234567890")]

known_image = face_recognition.load_image_file("Images/alberto_angela.jpg")
known_encoding = face_recognition.face_encodings(known_image)[0]
known_encodings_buffer += [(known_encoding, "Alberto Angela", "1122334455")]

known_image = face_recognition.load_image_file("Images/gerry_scotti.jpg")
known_encoding = face_recognition.face_encodings(known_image)[0]
known_encodings_buffer += [(known_encoding, "Gerry Scotti", "0000011111")]

# Inizializzazione contatore persone, time e intervallo
dest = "Images/captured_image.png"
presents = []
current_time = (datetime.datetime.now()).strftime("%Y-%m-%d %H:00:00")

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

# connessione al database
conn = psycopg2.connect(
    dbname="Iot",
    user="postgres",
    password="password",
    host="127.0.0.1",
    port="5432"
)
cur = conn.cursor()
print("Connected to database Iot")

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

def update_db_Accessi(giorno, ora, idpersona):
    cur.execute("""
                INSERT INTO "Accessi"(data, ora, persona)
                VALUES (%s, %s, %s)
                ON CONFLICT (data, persona) DO NOTHING
                """, (giorno, ora, idpersona,))
    conn.commit()
    print(f"[✓] Ingresso registrato nel database")

def compute_and_send():
    global results, recieved, dest, presents, current_time
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
            if answer[0]:
                name = encoding[1]
                idpersona = encoding[2]
                break
        if answer[0]:
            results = ("Si", name)
            data = datetime.datetime.now()
            ora = data.strftime("%H:00:00")
            giorno = data.strftime("%Y-%m-%d")
            data = data.strftime("%Y-%m-%d %H:00:00")
            if current_time != data:
                current_time = data
            #if idpersona not in presents:
            #    presents += [idpersona]
            update_db_Accessi(giorno, ora, idpersona)
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

# chiusura connessione database
cur.close()
conn.close()
