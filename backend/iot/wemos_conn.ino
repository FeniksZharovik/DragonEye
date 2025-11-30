#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClient.h>

const char* ssid = "CMCC-H17";
const char* password = "1234567899";

String serverUrl = "http://192.168.1.6:8000/device/receive";

WiFiClient client;

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("Connected!");
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;

    http.begin(client, serverUrl);
    http.addHeader("Content-Type", "application/json");

    String payload = "{\"weight\": 123, \"grade\": \"A\"}";
    int httpCode = http.POST(payload);

    if (httpCode > 0) {
      Serial.println(httpCode);
      Serial.println(http.getString());
    } else {
      Serial.println("HTTP request failed");
    }

    http.end();
  }

  delay(3000);
}
