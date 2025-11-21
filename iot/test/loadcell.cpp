#include "HX711.h"

#define DT  23
#define SCK 22

HX711 scale;

float calibration_factor = 400.40; // ganti sesuai hasil kalibrasi kamu

void setup() {
  Serial.begin(115200);
  scale.begin(DT, SCK);
  Serial.println("Menunggu stabilisasi load cell...");
  delay(2000);
  scale.set_scale(calibration_factor);
  scale.tare(); // set 0 saat tidak ada beban
  Serial.println("Load Cell Siap Digunakan!");
}

void loop() {
  if (scale.is_ready()) {
    float weight = scale.get_units(5); // rata-rata 5 pembacaan
    if (abs(weight) < 1) weight = 0; // biar 0 saat kosong
    Serial.print("Berat: ");
    Serial.print(weight, 2);
    Serial.println(" gram");
  } else {
    Serial.println("HX711 tidak terhubung!");
  }
  delay(500);
}
