# Progetto IoT
## Note:
  - installare librerie python presenti nel file **requirements.txt**

## Cosa fa recognition_full.py:
  - scatta foto utilizzando la telecamera del dispositivo
  - scatta foto ogni 3 sec e riconosce le somglianze dall'immagine salvata in memoria (le foto vengono poi cancellate)
  - riconosce somiglianze tra volti presenti in due immagini e risponde dicendo se sono lo stesso volto (con il nome della persona)
  - per fermare il programma: CTRL-C

## Cosa fa motion_detector.py
  - visualizza un video (telecamera o file)
  - calcola i cambiamenti avvenuti dal frame iniziale
  - riconosce gli oggetti che si sono mossi
  - aggiunto funzionamento per telecamera mobile
  - registra video solamente quando riconosce movimento (si disattiva dopo 5 secondi se non rileva piu' movimento)
  - comprime e salva video in /Videos
  - per fermare il programma: q. Per uscire e scartare il video: z

## To do:
  - implementare database con codice
  - fare in modo che una persona non venga riconosciuta 2 volte lo stesso giorno
  - resettare count quando cambia giorno
