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

# Inserire percorso delle immagini note (specificando id e nome della persona)
known_image = face_recognition.load_image_file("Images/ezio_greggio.jpg")
known_encoding = face_recognition.face_encodings(known_image)[0]
known_encodings_buffer += [(known_encoding, "Ezio Greggio", "1234567890")]

known_image = face_recognition.load_image_file("Images/alberto_angela.jpg")
known_encoding = face_recognition.face_encodings(known_image)[0]
known_encodings_buffer += [(known_encoding, "Alberto Angela", "1122334455")]

known_image = face_recognition.load_image_file("Images/gerry_scotti.jpg")
known_encoding = face_recognition.face_encodings(known_image)[0]
known_encodings_buffer += [(known_encoding, "Gerry Scotti", "0000011111")]

# Variabili tempo e percorso file
current_time = None
dest = None

# Variabili connessione mqtt
qos = 2
host = "127.0.0.1"
port = 1883
topic = "Images"
results = ("","")

# signal handler
stop = False

def handle_signal(signum, frame):
    global stop
    stop = True
    print("\nUscita...")

signal.signal(signal.SIGINT, handle_signal)

# Connessione al database
conn = psycopg2.connect(
    dbname = "Iot",
    user = "postgres",
    password = "",
    host = host,
    port = "5432"
)
cur = conn.cursor()
print("Connesso al database Iot")

def on_publish(client, userdata, mid, reason_code, properties):
    print("Risposta inviata (%d)" %mid)
    
def on_message(client, userdata, message):
    global dest, current_time
    current_time = (datetime.datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
    dest = "Images/unknown/unk-" + current_time + ".png"
    file = open(dest, "wb")
    file.write(message.payload)
    print("Immagine ricevuta")
    file.close()
    compute_and_send()
    
def on_connect(client, userdata, flags, reason_code, properties):
    global topic, qos
    if reason_code.is_failure:
        print(f"\nImpossibile connettersi al broker: {reason_code}.")
    else:
        client.subscribe(topic, qos)

def update_db_Accessi(giorno, ora, idpersona):
    cur.execute("""
                INSERT INTO "Accessi"(data, ora, persona)
                VALUES (%s, %s, %s)
                ON CONFLICT (data, persona) DO NOTHING
                """, (giorno, ora, idpersona,))
    conn.commit()
    print("Ingresso registrato nel database")

def update_db_Sconosciuti():
    global current_time
    cur.execute("""
                INSERT INTO "Sconosciuti"(tempo)
                VALUES (%s)
                ON CONFLICT (tempo) DO NOTHING
                """, (current_time,))
    conn.commit()
    print("Ingresso registrato nel database")

# Analizza l'immagine ricevuta e invia la risposta
def compute_and_send():
    global results, dest, current_time
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
        for encoding in known_encodings_buffer:
            answer = face_recognition.compare_faces([encoding[0]], unknown_encoding)
            if answer[0]:
                name = encoding[1]
                idpersona = encoding[2]
                break
        if answer[0]:
            results = ("Si", name)
            current_time = (datetime.datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
            giorno = current_time[:10]
            ora = current_time[11:]
            update_db_Accessi(giorno, ora, idpersona)
            try:
                os.remove(dest)
            except: pass
        else:
            results = ("No", "")
            update_db_Sconosciuti()
        print("L'immagine sconosciuta e' quella di una persona conosciuta:", results[0])

    mqttc.publish("Results/answer", results[0])
    mqttc.publish("Results/name", results[1])



mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_connect = on_connect
mqttc.on_publish = on_publish
mqttc.on_message = on_message

mqttc.connect(host, port)
while not stop:
    mqttc.loop()
# chiusura connessione database
cur.close()
conn.close()