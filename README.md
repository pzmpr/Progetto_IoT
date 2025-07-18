# Progetto IoT
## Note:
  - installare librerie python presenti nel file **requirements.txt**
  - face_recognition funziona solo su linux
  - configurare la connessione del database nei file **_server**

## Face recognition:
  - scatta foto utilizzando la telecamera del dispositivo
  - scatta foto ogni 5 sec e riconosce le somglianze dall'immagine salvata in memoria
  - riconosce somiglianze tra volti presenti in due immagini e risponde dicendo se sono lo stesso volto (con il nome della persona)
  - immagini senza volti vengono cancellate, immagini con volti sconosciuti vengono salvate in /Images/unknown
  - per fermare il programma: CTRL-C

## Recording
  - visualizza un video (telecamera o file)
  - calcola i cambiamenti avvenuti dal frame iniziale
  - riconosce gli oggetti che si sono mossi
  - registra video solamente quando riconosce movimento (si disattiva dopo 5 secondi se non rileva piu' movimento)
  - apre pagina web a indirizzo localhost:8000 con stream video a /video_feed
  - file html in /templates
  - comprime e salva video in /Videos
  - per fermare il programma: CTRL-C
