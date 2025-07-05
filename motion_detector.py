import argparse
import datetime
import imutils
import time
import cv2

# argomento
ap = argparse.ArgumentParser()
ap.add_argument("-a", "--min-area", type=int, default=500, help="minimum area size")
args = vars(ap.parse_args())

# lettura da webcam
cap = cv2.VideoCapture(0)

# creazione oggetto VideoWriter
fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = cv2.VideoWriter('Videos/output.avi', fourcc, 17.5, (640,  480)) # ! 4th arg: impostare la risoluzione della fotocamera
                                                                      # ! 3rd arg: velocita' video
time.sleep(2.0)
# inizializza primo frame nello stream video
firstFrame = None

text = "Libero"
active = False
timer = 50 # 5 secondi


# loop over the frames of the video
while True:

    # grab the current frame and initialize the occupied/unoccupied
    # text
    ret, frame = cap.read()
    if not ret:
        print("Impossibile ricevere frame. Uscita ...")
        break
    frame = frame if args.get("video", None) is None else frame[1]
    
    # scrittura stato della stanza e timestamo
    cv2.putText(frame, "Stato: {}".format(text), (10, 20),
        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
    cv2.putText(frame, datetime.datetime.now().strftime("%a %d %B %Y %H:%M:%S"),
        (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
    
    if text == "Occupato":
        active = True
        timer = 50
        # write frame
        out.write(frame)
    elif active:
        out.write(frame)
        timer -= 1
        if timer == 0:
            active = False
            timer = 50
    
    text = "Libero"
    
    # se non c'e' alcun frame, lo stream e' finito
    if frame is None:
        break
    
    # scala il frame, convertilo a scala di grigi, sfuoca
    frame = imutils.resize(frame, width=500)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)
    
    # se il primo frame e' None, inizializzalo
    if firstFrame is None:
        firstFrame = gray
        continue


    # calcola il valore assoluto della differenza tra il frame attuale e quello precedente
    frameDelta = cv2.absdiff(firstFrame, gray)
    # aggiorna il frame precedente con l'ultimo frame
    firstFrame = gray
    thresh = cv2.threshold(frameDelta, 25, 255, cv2.THRESH_BINARY)[1] # NOTE: cambia secondo argomento se riconosce micromovimenti
    # dilata l'immagine soglia per riempire i buchi, poi trova i contorni
    # nell'immagine soglia
    thresh = cv2.dilate(thresh, None, iterations=2)
    cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)  
    # cicla sui contorni
    for c in cnts:
        # se il contorno e' troppo piccolo, ignoralo
        if cv2.contourArea(c) < args["min_area"]:
            continue
        # calcola la bounding box per il contorno, disegnala sul frame,
        # aggiorna il testo
        (x, y, w, h) = cv2.boundingRect(c)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        text = "Occupato"


    # mostra il frame attuale
    cv2.imshow("Thresh", thresh)
    cv2.imshow("Frame Delta", frameDelta)
    cv2.imshow("Security Feed", frame)
    key = cv2.waitKey(1) & 0xFF
    # pressione tasto 'q' -> uscita
    if key == ord("q"):
        break


# pulizia finestre / chiusura telecamera
cap.release()
out.release()
cv2.destroyAllWindows()
