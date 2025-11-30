import paho.mqtt.client as mqtt
import threading

BROKER = "10.120.200.21"

# Topik dari ESP32
TOPIC_WEIGHT = "iot/machine/weight"
TOPIC_GRADE  = "iot/machine/grade"

# Topik untuk kirim grade ke ESP32
TOPIC_PY_GRADE = "iot/python/grade"


# MQTT CALLBACK
def on_connect(client, userdata, flags, rc):
    print("Terhubung ke MQTT Broker, kode:", rc)
    client.subscribe(TOPIC_WEIGHT)
    client.subscribe(TOPIC_GRADE)
    print("Menunggu data dari ESP32...\n")

def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()

    if topic == TOPIC_WEIGHT:
        print(f"[BERAT] {payload} gram")

    elif topic == TOPIC_GRADE:
        print(f"[GRADE OTOMATIS] {payload}")


# FUNGSI KIRIM GRADE
def kirim_grade(grade):
    client.publish(TOPIC_PY_GRADE, grade)
    print(f">>> Grade '{grade}' terkirim ke ESP32\n")


# THREAD UNTUK INPUT TERMINAL
def input_terminal():
    while True:
        g = input("Masukkan grade (A/B/C) : ").upper()

        if g in ["A", "B", "C"]:
            kirim_grade(g)
        else:
            print("Input tidak valid! Gunakan A / B / C.\n")


# SETUP MQTT
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

print("Menghubungkan ke MQTT broker...")
client.connect(BROKER, 1883, 60)

# Jalankan thread input
threading.Thread(target=input_terminal, daemon=True).start()

# MQTT loop
client.loop_forever()