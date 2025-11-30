# mqtt_service.py

import json
import time
import threading
import paho.mqtt.client as mqtt

# ============================================================
# MQTT CONFIGURATION
# ============================================================

MQTT_BROKER = "localhost"  # MQTT Broker address
MQTT_PORT = 1883           # MQTT Broker port
MQTT_TOPIC_SUBSCRIBE = "device/status"  # Topic to subscribe
MQTT_TOPIC_PUBLISH = "device/command"  # Topic to publish messages

# MQTT Client initialization
client = mqtt.Client()

# ============================================================
# CALLBACK HANDLERS
# ============================================================

def on_connect(client, userdata, flags, rc):
    """
    This callback function is called when the MQTT client connects to the broker.
    """
    if rc == 0:
        print("✅ MQTT Connected successfully")
        client.subscribe(MQTT_TOPIC_SUBSCRIBE)
        print(f"📩 Subscribed to topic: {MQTT_TOPIC_SUBSCRIBE}")
    else:
        print(f"❌ MQTT Connection failed. Code: {rc}")

def on_message(client, userdata, msg):
    """
    This callback function is called when the MQTT client receives a message.
    """
    try:
        payload = msg.payload.decode()
        print(f"📥 MQTT Received [{msg.topic}]: {payload}")
    except Exception as e:
        print(f"❌ Error decoding MQTT message: {e}")

# Setting callback functions
client.on_connect = on_connect
client.on_message = on_message

# ============================================================
# MQTT STARTER FUNCTION
# ============================================================

def start_mqtt():
    """
    Start the MQTT client and connect to the broker.
    Run the MQTT loop in a background thread.
    """
    print("🔄 Starting MQTT client...")

    try:
        # Connect to MQTT broker
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
    except Exception as e:
        print(f"❌ MQTT Connection Error: {e}")
        return

    # Running MQTT loop in a separate thread to prevent blocking
    thread = threading.Thread(target=client.loop_forever)
    thread.daemon = True  # Daemon thread will exit when the main program exits
    thread.start()

    print("🚀 MQTT client is now running.")

# ============================================================
# PUBLISH FUNCTION
# ============================================================

def publish(topic: str, message: dict):
    """
    General function to publish a message to an MQTT topic.
    """
    try:
        payload = json.dumps(message)  # Convert dictionary to JSON string
        client.publish(topic, payload)
        print(f"📤 MQTT Publish → topic={topic} | message={payload}")
    except Exception as e:
        print(f"❌ MQTT Publish Error: {e}")

def publish_command(command: dict):
    """
    Publish command message to the default device topic.
    """
    publish(MQTT_TOPIC_PUBLISH, command)

# ============================================================
# AUTO START MQTT
# ============================================================

# Automatically start MQTT when the FastAPI application starts
start_mqtt()