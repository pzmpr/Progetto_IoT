import paho.mqtt.client as mqtt
from random import randrange, uniform
import time
import signal
import sys

shutdown = False

def signal_handler(signal, frame):
        global shutdown
        shutdown = True
        print('You pressed Ctrl+C!\nExiting...')

signal.signal(signal.SIGINT, signal_handler)
print('Press Ctrl+C to stop and exit!')


def on_publish(client, userdata, mid, reason_code, properties):
    print('Message published (%d)' %mid)
    
    
mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_publish = on_publish

mqttc.connect("127.0.0.1",1883)

mqttc.loop_start()
while not shutdown:
    file = open("img.jpg", "rb")
    fileContent = file.read()
    byteArr = bytearray(fileContent)
    mqttc.publish("IMAGES", byteArr)
    file.close()
    time.sleep(5)
    #mqttc.disconnect()
mqttc.loop_stop()
sys.exit(0)