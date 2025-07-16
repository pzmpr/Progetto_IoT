import cv2
import threading
import paho.mqtt.client as mqtt
import signal

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)  # create new instance
host = "127.0.0.1"
port = 1883

# signal handler
stop = False

def handle_signal(signum, frame):
    global stop
    stop = True
    print("\nExiting...")

signal.signal(signal.SIGINT, handle_signal)

def start_streaming():
    streaming_thread.start()

def stream():
    global stop
    print("Streaming from video source : 0")
    while not stop:
        _ , img = cam.read()
        img_str = cv2.imencode('.jpg', img)[1].tobytes()
        client.publish(topic, img_str)

client.connect(host, port)
topic = "Video"
cam = cv2.VideoCapture(0)

streaming_thread = threading.Thread(target=stream())
