import paho.mqtt.client as mqtt

BROKER = "10.120.200.89"
TOPIC  = "iot/machine/grade"

# --- Setup MQTT Client ---
client = mqtt.Client()
client.connect(BROKER, 1883, 60)

def send_grade(grade: str):
    """
    Mengirim grade (A/B/C) ke MQTT broker.
    Dipanggil langsung dari camera.py
    """
    grade = grade.upper()

    if grade not in ["A", "B", "C"]:
        print("[MQTT] Grade tidak valid, tidak terkirim:", grade)
        return

    client.publish(TOPIC, grade)
    print(f"[MQTT] Grade terkirim: {grade}")
