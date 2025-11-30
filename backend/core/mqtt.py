# core/mqtt.py

import os
import json
import threading
import logging
import time
from typing import Callable, Optional
import paho.mqtt.client as mqtt_client

log = logging.getLogger("core.mqtt")
logging.basicConfig(level=logging.INFO)

# Load config from .env
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USER = os.getenv("MQTT_USER", "").strip()
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "").strip()
MQTT_TLS = os.getenv("MQTT_TLS", "0") == "1"

WEIGHT_TOPIC = "iot/machine/weight"
GRADE_TOPIC = "iot/machine/grade"
COMMAND_TOPIC_TEMPLATE = os.getenv("COMMAND_TOPIC_TEMPLATE", "iot/device/{device_id}/command")

CLIENT_ID = os.getenv("MQTT_CLIENT_ID", "fastapi-backend")

# Global state with thread safety
mqttGrade = None
mqttWeight = None
currentWeight = None  # Current weight tracking
previousWeight = None  # Previous weight for delta calculation
weightTimestamp = None  # Timestamp of last weight update
_state_lock = threading.Lock()

def get_mqtt_weight():
    with _state_lock:
        return mqttWeight

def set_mqtt_weight(value):
    global mqttWeight
    with _state_lock:
        mqttWeight = value

def get_mqtt_grade():
    with _state_lock:
        return mqttGrade

def set_mqtt_grade(value):
    global mqttGrade
    with _state_lock:
        mqttGrade = value

def get_current_weight():
    """Get the current weight value."""
    with _state_lock:
        return currentWeight

def set_current_weight(value):
    """Set the current weight and update timestamp."""
    global currentWeight, previousWeight, weightTimestamp
    with _state_lock:
        previousWeight = currentWeight
        currentWeight = value
        weightTimestamp = time.time()

def get_weight_delta():
    """Get the difference between current and previous weight."""
    with _state_lock:
        if previousWeight is None or currentWeight is None:
            return 0
        return currentWeight - previousWeight

def get_weight_info():
    """Get comprehensive weight information."""
    with _state_lock:
        return {
            "current": currentWeight,
            "previous": previousWeight,
            "delta": (currentWeight - previousWeight) if (previousWeight and currentWeight) else 0,
            "timestamp": weightTimestamp
        }

# Create client
client = mqtt_client.Client(client_id=CLIENT_ID, protocol=mqtt_client.MQTTv311)
_client_started = False
_client_lock = threading.Lock()

# Weight handlers registry
_weight_handlers = []

def register_weight_handler(fn: Callable[[float, dict], None]):
    """Register a callback for weight updates: fn(weight_float, meta_dict)."""
    _weight_handlers.append(fn)
    log.info("Registered weight handler: %s", fn.__name__)

def _safe_parse_weight_payload(payload: str) -> Optional[float]:
    """Try to parse different payload formats into float weight, or return None."""
    if payload is None:
        return None
    payload = payload.strip()
    # Direct numeric string
    try:
        return float(payload)
    except ValueError:
        pass
    # Try JSON
    try:
        data = json.loads(payload)
        if isinstance(data, (int, float)):
            return float(data)
        if isinstance(data, dict):
            for k in ("weight", "bobot", "value", "w"):
                if k in data:
                    try:
                        return float(data[k])
                    except Exception:
                        continue
        # Maybe nested list/number
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], (int, float)):
            return float(data[0])
    except Exception:
        pass
    return None

def on_message(_client, userdata, msg):
    try:
        payload = msg.payload.decode(errors="ignore").strip()
        log.debug("MQTT message on %s: %s", msg.topic, payload)

        if msg.topic == WEIGHT_TOPIC:
            bobot = _safe_parse_weight_payload(payload)
            if bobot is None:
                log.warning("Unrecognized weight payload format: %s", payload)
                return
            
            # Update all weight states
            set_mqtt_weight(bobot)
            set_current_weight(bobot)
            
            log.info("💾 Updated weight: current=%s, delta=%s", bobot, get_weight_delta())
            
            # Call registered handlers
            meta = {
                "topic": msg.topic,
                "current": get_current_weight(),
                "previous": previousWeight,
                "delta": get_weight_delta(),
                "timestamp": weightTimestamp
            }
            for h in list(_weight_handlers):
                try:
                    h(bobot, meta)
                except Exception as e:
                    log.exception("Weight handler error: %s", e)
    except Exception as e:
        log.exception("Error handling MQTT message: %s", e)

def on_connect(_client, userdata, flags, rc):
    if rc == 0:
        log.info("✅ Connected to Mosquitto MQTT Broker")
        _client.subscribe(WEIGHT_TOPIC)
        log.info("📚 Subscribed to: %s", WEIGHT_TOPIC)
    else:
        log.error("❌ MQTT connection failed with code %s", rc)

def on_disconnect(client_obj, userdata, rc):
    log.warning("MQTT disconnected (rc=%s). Attempting reconnect...", rc)
    try:
        client_obj.reconnect()
    except Exception as e:
        log.debug("Reconnect attempt failed: %s", e)

def publish_grade(grade: str, qos: int = 1, retain: bool = True) -> bool:
    try:
        set_mqtt_grade(grade)
        payload = json.dumps({"grade": grade})
        result = client.publish(GRADE_TOPIC, payload, qos=qos, retain=retain)
        ok = (result.rc == mqtt_client.MQTT_ERR_SUCCESS)
        if ok:
            log.info("📤 Published grade '%s' to %s", grade, GRADE_TOPIC)
        else:
            log.warning("Failed publish (rc=%s) for grade '%s'", result.rc, grade)
        return ok
    except Exception as e:
        log.exception("publish_grade error: %s", e)
        return False

def publish_command(device_id: str, payload: dict, qos: int = 1, retain: bool = False) -> bool:
    """Publish a command to a specific device."""
    topic = COMMAND_TOPIC_TEMPLATE.format(device_id=device_id)
    try:
        result = client.publish(topic, json.dumps(payload), qos=qos, retain=retain)
        ok = (result.rc == mqtt_client.MQTT_ERR_SUCCESS)
        if ok:
            log.info("📤 Published command to %s", topic)
        else:
            log.warning("Publish command failed rc=%s", result.rc)
        return ok
    except Exception as e:
        log.exception("publish_command error: %s", e)
        return False

def init_mqtt(start_thread: bool = True, keepalive: int = 60, will_topic: Optional[str] = None):
    """Initialize and start MQTT client in background."""
    global _client_started

    with _client_lock:
        if _client_started:
            log.debug("MQTT already started")
            return

        if MQTT_USER and MQTT_PASSWORD:
            client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
        
        if MQTT_TLS:
            import ssl
            client.tls_set(tls_version=ssl.PROTOCOL_TLS)

        if will_topic:
            client.will_set(will_topic, json.dumps({"status": "offline", "client": CLIENT_ID}), retain=True, qos=1)

        client.on_connect = on_connect
        client.on_message = on_message
        client.on_disconnect = on_disconnect

        def run():
            try:
                client.connect(MQTT_BROKER, MQTT_PORT, keepalive=keepalive)
                client.loop_forever()
            except Exception as e:
                log.exception("MQTT connection error: %s", e)

        if start_thread:
            thread = threading.Thread(target=run, daemon=True)
            thread.start()
            _client_started = True
            log.info("🧵 MQTT background thread started → %s:%s", MQTT_BROKER, MQTT_PORT)

def shutdown_mqtt():
    """Stop loop and disconnect cleanly (call on app shutdown)."""
    global _client_started
    with _client_lock:
        if not _client_started:
            return
        try:
            client.loop_stop()
            client.disconnect()
        except Exception as e:
            log.debug("Error during MQTT shutdown: %s", e)
        _client_started = False
        log.info("MQTT stopped")


