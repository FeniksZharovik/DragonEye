// Sketch Kalibrasi HX711 - Hitung calibration_factor otomatis
#include "HX711.h"

#define DT  3
#define SCK 2

HX711 scale;
const int NUM_SAMPLES = 15; // jumlah pembacaan untuk rata-rata

void setup() {
  Serial.begin(115200);
  scale.begin(DT, SCK);
  Serial.println(F("=== Kalibrasi HX711 ==="));
  Serial.println(F("1) Pastikan load cell kosong. Tekan 't' di Serial Monitor untuk tare (set 0)."));
  Serial.println(F("2) Setelah tare, letakkan beban yang diketahui (mis. 1000 gram)."));
  Serial.println(F("3) Masukkan berat beban di Serial Monitor (dalam gram), lalu tekan enter."));
}

long averageReading(int n) {
  long sum = 0;
  for (int i=0;i<n;i++) {
    while (!scale.is_ready()) delay(1);
    sum += scale.read();
    delay(50);
  }
  return sum / n;
}

void loop() {
  if (Serial.available()) {
    String s = Serial.readStringUntil('\n');
    s.trim();
    if (s == "t" || s == "T") {
      Serial.println(F("Tare: Membaca offset (kosong)..."));
      long off = averageReading(NUM_SAMPLES);
      // HX711 library punya fungsi tare() juga, kita simpan offset manual untuk info
      Serial.print(F("Offset (raw average saat kosong): "));
      Serial.println(off);
      Serial.println(F("Sekarang letakkan beban yang diketahui dan masukkan nilainya (gram)."));
      return;
    }
    // Anggap input adalah angka = berat yang diketahui
    float knownWeight = s.toFloat();
    if (knownWeight <= 0) {
      Serial.println(F("Berat tidak valid. Masukkan angka (gram)."));
      return;
    }

    Serial.println(F("Membaca offset (kosong) sekali lagi..."));
    long offset = averageReading(NUM_SAMPLES);
    Serial.print(F("Offset (raw): "));
    Serial.println(offset);

    Serial.println(F("Sekarang baca dengan beban terpasang..."));
    delay(1500); // beri waktu pasang beban
    long reading = averageReading(NUM_SAMPLES);
    Serial.print(F("Reading dengan beban (raw): "));
    Serial.println(reading);

    long net = reading - offset;
    Serial.print(F("Net (reading - offset): "));
    Serial.println(net);

    // Faktor kalibrasi sesuai library HX711: units = net / scale => scale = net / knownWeight
    float calibration_factor = (float)net / knownWeight;
    Serial.print(F("Calculated calibration_factor: "));
    Serial.println(calibration_factor, 6);

    Serial.println(F("COPY nilai calibration_factor ini ke kode utama (set_scale)."));
    Serial.println(F("Contoh: float calibration_factor = 826.12;"));
    Serial.println(F("Selesai."));
  }
}