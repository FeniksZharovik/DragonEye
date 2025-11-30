import paho.mqtt.client as mqtt
import time

broker = "10.120.200.89"
topic = "iot/machine/grade"

client = mqtt.Client()
client.connect(broker, 1883, 60)

while True:
    grade = input("Masukkan Grade (A/B/C): ").upper()

    if grade not in ["A", "B", "C"]:
        print("Grade tidak valid!")
        continue

    client.publish(topic, grade)
    print("Terkirim:", grade)
    time.sleep(0.2)
