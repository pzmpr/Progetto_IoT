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
prev_encoding = None

# Inserire percorso delle immagini note (specificando id e nome della persona)
known_image = face_recognition.load_image_file("Images/1234567890.jpg")
known_encoding = face_recognition.face_encodings(known_image)[0]
known_encodings_buffer += [(known_encoding, "Ezio Greggio", "1234567890")]

known_image = face_recognition.load_image_file("Images/1122334455.jpg")
known_encoding = face_recognition.face_encodings(known_image)[0]
known_encodings_buffer += [(known_encoding, "Alberto Angela", "1122334455")]

known_image = face_recognition.load_image_file("Images/0000011111.jpg")
known_encoding = face_recognition.face_encodings(known_image)[0]
known_encodings_buffer += [(known_encoding, "Gerry Scotti", "0000011111")]

# Variabili tempo e percorso file
current_time = None
dest = None

# Variabili connessione mqtt
qos  = 2
host = "127.0.0.1"
port = 1883
sub_topic  = "Images/content"
pub_topic1 = "Images/Results/answer"
pub_topic2 = "Images/Results/name"
results = ("","")

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

# Connessione al database
conn = psycopg2.connect(
    dbname   = "Iot",
    user     = "postgres",
    password = "",
    host     = host,
    port     = "5432"
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
    global sub_topic, qos
    if reason_code.is_failure:
        print(f"\nImpossibile connettersi al broker: {reason_code}.")
    else:
        client.subscribe(sub_topic, qos)

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
    global results, dest, current_time, prev_encoding, pub_topic1, pub_topic2
    unknown_image = face_recognition.load_image_file(dest)
    # non sono stati riconosciuti volti nell'immagine
    if( len(face_recognition.face_encodings(unknown_image)) == 0 ):
        print("Non e' stato riconosciuto alcun volto")
        results = ("NA", "NA")
        remove_file(dest)
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
            print("L'immagine sconosciuta e' quella di una persona conosciuta:", results[0])
            update_db_Accessi(giorno, ora, idpersona)
            remove_file(dest)
        else:
            results = ("No", "")
            print("L'immagine sconosciuta e' quella di una persona conosciuta:", results[0])
            # controlla che il volto non sia quello dell'immagine precedente
            if prev_encoding is None:
                update_db_Sconosciuti()
            elif not (face_recognition.compare_faces([prev_encoding], unknown_encoding))[0]:
                update_db_Sconosciuti()
            else:
                remove_file(dest)
            prev_encoding = unknown_encoding
    mqttc.publish(pub_topic1, results[0])
    mqttc.publish(pub_topic2, results[1])



mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_connect = on_connect
mqttc.on_publish = on_publish
mqttc.on_message = on_message

mqttc.connect(host, port)
while not stop:
    mqttc.loop()
mqttc.disconnect()
# chiusura connessione database
cur.close()
conn.close()
