import paho.mqtt.client as mqtt
import signal

def on_subscribe(client, userdata, mid, reason_code_list, properties):
    # Since we subscribed only for a single channel, reason_code_list contains
    # a single entry
    if reason_code_list[0].is_failure:
        print(f"\nBroker rejected you subscription: {reason_code_list[0]}")
    else:
        print(f"\nBroker granted the following QoS: {reason_code_list[0].value}")
        
def on_connect(client, userdata, flags, reason_code, properties):
    global topic, qos
    if reason_code.is_failure:
        print(f"\nFailed to connect: {reason_code}. loop_forever() will retry connection")
    else:
        # we should always subscribe from on_connect callback to be sure
        # our subscribed is persisted across reconnections.
        client.subscribe('IMAGES',qos)
    
def on_message(client, userdata, message):
    file = open('images/img.jpg', "wb")
    file.write(message.payload)
    print("Image Received")
    file.close()

def signal_handler(sig, frame):
		global mqttc, flag_is_connected
		print('\nCtrl+C detected!')
		if flag_is_connected:
			mqttc.unsubscribe('IMAGES')
			mqttc.disconnect()

signal.signal(signal.SIGINT, signal_handler)

flag_is_connected=False
qos=2
broker_address="127.0.0.1"

mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_connect = on_connect
mqttc.on_message = on_message
mqttc.on_subscribe = on_subscribe

mqttc.user_data_set([])
mqttc.connect(broker_address)
flag_is_connected=True
mqttc.loop_forever()
print(f"\nReceived the following message(s): {mqttc.user_data_get()}")