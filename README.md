# Progetto IoT
## Note:
  - face_recognition funziona solo su linux e macos

## Face recognition:
  - scatta foto utilizzando la telecamera del dispositivo
  - scatta foto ogni 5 sec e riconosce le somglianze dall'immagine salvata in memoria
  - riconosce somiglianze tra volti presenti in due immagini e risponde dicendo se sono lo stesso volto (con il nome della persona)
  - immagini senza volti vengono cancellate, immagini con volti sconosciuti vengono salvate in /Images/unknown
  - per fermare il programma: CTRL-C

## Recording
  - registra un video (telecamera)
  - calcola i cambiamenti avvenuti dal frame iniziale
  - riconosce gli oggetti che si sono mossi
  - registra video solamente quando riconosce movimento (si disattiva dopo 5 secondi se non rileva piu' movimento)
  - apre pagina web a indirizzo localhost:8000 con stream video a /video_feed
  - file html in /templates
  - comprime e salva video in /Videos
  - per fermare il programma: CTRL-C

## Setup
  - installare librerie python presenti nel file **requirements.txt** (se dlib dà problemi installare cmake senza pip)
    
          pip install -r requirements.txt
  - creare il database con il file **DB_iot.txt** su OneDrive
  - aprire la connessione al database postgresql (127.0.0.1:5432)
  - [opzionale] aggiungere dati utenti riconosciuti nel database e in **face_recognition_pc.py** e rispettive immagini nella directory /Images
  - creare la dashboard su grafana importando il file **dashboard_grafana_iot.json**
  - configurare la connessione del database nei file **_pc**
  - configurare indirizzo ip dell'host nei file **_rpi**
  - modificare risoluzione telecamera e soglia nei file **motion_detector_**
  - eseguire gli script python nelle rispettive directory

## Configurazione mosquitto
  per configurare mosquitto per connessioni su LAN:
  - modificare file mosquitto.config nella cartella di installazione di mosquitto (\# -> commenti) <br>
    inserire/modificare le righe

        accept_anonymous true
        listener 1883 0.0.0.0
  - caricare il file di configurazione (su docker invece caricare il file con -v)

        mosquitto -c /{path}/mosquitto.conf

  da docker invece di specificare le porte (-p) specificare la connessione (--network host) per connessione LAN
## Configurazione postgres
> docker pull postgres

> docker run --name postgres-db \
  -e POSTGRES_PASSWORD=1234 \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_DB=Iot \
  -p 5432:5432 \
  -v postgres-data:/var/lib/postgresql/data \
  -d postgres
  
> docker exec -it postgres-db psql -U postgres -d Iot -f DB_iot.sql

modificare postgres.conf <br>
modificare pg_hba.conf inserendo indirizzi e porte

https://medium.com/@yeyangg/configuring-postgresql-for-lan-network-access-2023-fcbd2df4a157

## Creazione rete docker
> docker network create \<nome-rete\>

> docker network connect \<nome-rete\> \<container\>

Connessione: \<nome-container\>:\<porta\>

## Configurazione grafana
> docker run -d --name=grafana -p 3000:3000 grafana/grafana

- creare account
- creare connessione a database
- importare file dashboard-grafana.json
