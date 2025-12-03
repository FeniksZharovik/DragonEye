import paho.mqtt.client as mqtt

# KONFIGURASI MQTT
MQTT_BROKER = "10.204.14.89"     # Samakan dengan ESP32
MQTT_PORT   = 1883
TOPIC_WEIGHT = "iot/machine/weight"   # Data dari load cell

# CALLBACK KETIKA TERHUBUNG
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✓ Terhubung ke MQTT broker")
        client.subscribe(TOPIC_WEIGHT)
        print(f"✓ Subscribe ke topik: {TOPIC_WEIGHT}")
    else:
        print("✗ Gagal terhubung, kode:", rc)

# CALLBACK KETIKA ADA DATA MASUK
def on_message(client, userdata, msg):
    bobot = msg.payload.decode()
    print(f"[MQTT] Berat diterima: {bobot} gram")

# MAIN
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

print("Menghubungkan ke MQTT...")
client.connect(MQTT_BROKER, MQTT_PORT, 60)

# loop forever menunggu data
client.loop_forever()