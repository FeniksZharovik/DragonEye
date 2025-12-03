#include <WiFi.h>
#include <PubSubClient.h>
#include <ESP32Servo.h>
#include "HX711.h"

// ----------------------------
// WIFI & MQTT SETUP
// ----------------------------
const char* ssid = "mqtt";
const char* password = "12345678";
const char* mqtt_server = "10.204.14.89";

WiFiClient espClient;
PubSubClient client(espClient);

// ----------------------------
// LOAD CELL
// ----------------------------
#define DT  23
#define SCK 22
HX711 scale;

float calibration_factor = 400;   // sesuaikan jika perlu


// ----------------------------
// SERVO & MOTOR
// ----------------------------
#define SERVO_PENDORONG 13  
#define SERVO_B         12
#define SERVO_C         14
#define PIN_MOTOR       26

Servo servoPendorong;
Servo servoB;
Servo servoC;


// ----------------------------
// FUNGSI DORONG
// ----------------------------
void servoDorong() {
  servoPendorong.write(45);
  delay(2000);
  servoPendorong.write(180);
}


// ----------------------------
// CALLBACK MENERIMA GRADE
// ----------------------------
void callback(char* topic, byte* message, unsigned int length) {

  Serial.print("Pesan masuk [");
  Serial.print(topic);
  Serial.print("]: ");

  String grade = "";
  for (int i = 0; i < length; i++) {
    grade += (char)message[i];
  }
  Serial.println(grade);

  // Eksekusi servo sesuai grade
  if (grade == "A") {
    Serial.println("== Eksekusi Grade A ==");
    servoDorong();
    digitalWrite(PIN_MOTOR, HIGH);
    delay(4000);
    digitalWrite(PIN_MOTOR, LOW);
  }

  else if (grade == "B") {
    Serial.println("== Eksekusi Grade B ==");
    servoB.write(55);
    servoDorong();
    digitalWrite(PIN_MOTOR, HIGH);
    delay(3000);
    digitalWrite(PIN_MOTOR, LOW);
    servoB.write(0);
  }

  else if (grade == "C") {
    Serial.println("== Eksekusi Grade C ==");
    servoC.write(55);
    servoDorong();
    digitalWrite(PIN_MOTOR, HIGH);
    delay(1500);
    digitalWrite(PIN_MOTOR, LOW);
    servoC.write(5);
  }

  else {
    Serial.println("Grade tidak dikenal!");
  }
}


// ----------------------------
// MQTT RECONNECT
// ----------------------------
void reconnect() {
  while (!client.connected()) {
    Serial.println("Menghubungkan MQTT...");

    if (client.connect("ESP32_Grading")) {
      Serial.println("Terhubung!");
      client.subscribe("iot/machine/grade");   // SUBSCRIBE untuk grade Python
    } else {
      Serial.print("Gagal, rc=");
      Serial.print(client.state());
      Serial.println(" coba lagi 3 detik...");
      delay(3000);
    }
  }
}


// ----------------------------
// SETUP
// ----------------------------
void setup() {
  Serial.begin(115200);

  // WIFI
  Serial.println("Menghubungkan WiFi...");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi Terhubung!");
  Serial.println(WiFi.localIP());

  // MQTT
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);

  // LOAD CELL
  scale.begin(DT, SCK);
  Serial.println("Menunggu stabilisasi load cell...");
  delay(3000);
  scale.set_scale(calibration_factor);
  scale.tare();
  Serial.println("Load Cell Siap!\n");

  // SERVO
  servoPendorong.attach(SERVO_PENDORONG);
  servoB.attach(SERVO_B);
  servoC.attach(SERVO_C);

  pinMode(PIN_MOTOR, OUTPUT);
  digitalWrite(PIN_MOTOR, LOW);

  // posisi awal
  servoPendorong.write(180);
  servoB.write(0);
  servoC.write(5);

  Serial.println("=== Sistem Grading Mode Python + Loadcell Realtime ===");
}


// ----------------------------
// LOOP
// ----------------------------
void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  // ----------------------------
  // TAMPILKAN LOADCELL REALTIME
  // ----------------------------
  if (scale.is_ready()) {
    float weight = scale.get_units(5);

    if (abs(weight) < 1) weight = 0;

    Serial.print("Berat: ");
    Serial.print(weight, 2);
    Serial.println(" gram");

    // Kirim realtime ke MQTT
    char msg[10];
    dtostrf(weight, 1, 2, msg);
    client.publish("iot/machine/weight", msg);

  } else {
    Serial.println("Loadcell belum siap...");
  }

  delay(200);  // supaya serial tidak terlalu cepat
}
