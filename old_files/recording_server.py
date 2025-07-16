import cv2 as cv
import threading
import numpy as np
import paho.mqtt.client as mqtt

fourcc = cv.VideoWriter_fourcc(*'DIVX')
out = cv.VideoWriter('Video/output.avi', fourcc, 10.0, (640,  480))

host = "127.0.0.1"
port = 1883
topic = "Video"
frame = None  # empty variable to store latest message received


def subscribe():
    global client
    client.loop_forever() # Start networking daemon
    
def on_connect(client, userdata, flags, reason_code, properties):  # The callback for when the client connects to the broker
    global topic
    client.subscribe(topic)  # Subscribe to the topic, receive any messages published on it
    print("Subscring to topic :", topic)

def on_message(client, userdata, msg):  # The callback for when a PUBLISH message is received from the server.
    global out, frame
    nparr = np.frombuffer(msg.payload, np.uint8)
    frame = cv.imdecode(nparr,  cv.IMREAD_COLOR)
    frame = cv.resize(frame, (640,480))   # just in case you want to resize the viewing area
    out.write(frame)
    cv.imshow('recv', frame)
    if cv.waitKey(1) & 0xFF == ord('q'):
        return


client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)  # Create instance of client 
client.on_connect = on_connect  # Define callback function for successful connection
client.message_callback_add(topic, on_message)
client.connect(host,port)  # connecting to the broking server
        

t = threading.Thread(target=subscribe())       # make a thread to loop for subscribing
t.start() # run this thread