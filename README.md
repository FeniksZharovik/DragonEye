```
sortir-jagung/
│
├── raw_data/                         # Dataset mentah (hasil foto HP)
│   ├── grade_a/                      # Jagung kualitas bagus (Grade A)
│   ├── grade_b/                      # Jagung kualitas sedang (Grade B)
│   └── grade_c/                      # Jagung kualitas rendah (Grade C)
│
├── dataset/                          # Dataset hasil preprocessing
│   ├── grade_a/                      # Hasil preprocess jagung Grade A
│   ├── grade_b/                      # Hasil preprocess jagung Grade B
│   └── grade_c/                      # Hasil preprocess jagung Grade C
│
├── preprocessing/                    # Modul PCV
│   └── preprocess_images.py          # Script utama preprocessing (resize, normalisasi, augmentasi)
│
├── model/                            # Modul Sistem Kecerdasan (AI/Deep Learning)
│   ├── train_model.ipynb             # Notebook training CNN/ResNet/MobileNet
│   ├── evaluate_model.py             # Script evaluasi (akurasi, confusion matrix, F1-score)
│   ├── model.h5                      # Model hasil training format Keras/TensorFlow
│   └── model.tflite                  # Model versi ringan untuk IoT (ESP32/Raspberry Pi)
│
├── classification/                   # Modul inferensi (real-time klasifikasi)
│   ├── classify_realtime.py          # Jalankan klasifikasi via webcam (real-time)
│   └── test_single_image.py          # Uji klasifikasi untuk 1 gambar
│
├── iot/                              # Modul IoT
│   ├── esp32_iot.ino                 # Kode ESP32 untuk kirim hasil klasifikasi ke cloud
│   ├── mqtt_publisher.py             # Python: publish data ke MQTT broker/Firebase
│   └── mqtt_subscriber.py            # Python: subscriber untuk monitoring data
│
├── dashboard/                        # Modul monitoring hasil sortir
│   ├── web_dashboard/                # Dashboard berbasis web
│   │   ├── index.html                # Tampilan utama dashboard
│   │   ├── style.css                 # Styling web
│   │   └── app.js                    # Script ambil data dari MQTT/Firebase
│   └── mobile_app/                   # (Opsional) Aplikasi Android
│       └── mit_app_inventor.aia      # File project MIT App Inventor
│
├── actuator/                         # Modul sortir fisik (opsional)
│   └── servo_control.ino             # Kode servo/motor untuk sortir buah jagung
│
├── requirements.txt                  # Daftar library Python (OpenCV, TensorFlow, MQTT, dll.)
└── README.md                         # Dokumentasi utama project
```
1. PCV (Pengolahan Citra & Vision)
```
preprocessing/preprocess_images.py
Fokus: pengambilan gambar buah jagung, segmentasi citra, preprocessing.
```

2. Sistem Kecerdasan (AI/ML)
```
model/train_model.ipynb (training CNN/ResNet/MobileNet)
model/evaluate_model.py (evaluasi akurasi model)
classification/classify_realtime.py (klasifikasi buah jagung real-time menjadi Grade A, B, C)
Fokus: klasifikasi kualitas jagung dengan deep learning.
```
3. IoT
```
iot/esp32_iot.ino (ESP32 kirim hasil sortir ke cloud)
iot/mqtt_publisher.py + mqtt_subscriber.py (komunikasi data)
dashboard/web_dashboard/ (dashboard real-time menampilkan jumlah jagung per grade)
actuator/servo_control.ino (opsional: mekanisme sortir fisik ke wadah A, B, C)
```

## Roadmap Proyek

### Tahap 1 – Perencanaan Sistem
- Menentukan kebutuhan sistem: klasifikasi buah jagung menjadi Grade A, B, C.  
- Menyusun arsitektur sistem: PCV, AI, IoT, aktuator (opsional).  
- Menentukan perangkat keras: kamera, ESP32/Raspberry Pi, motor/servo.

### Tahap 2 – Dataset & Preprocessing
- **Pengumpulan Data**  
  - Foto buah jagung utuh dari berbagai kondisi (Grade A, B, C).  
  - Minimal 300–500 citra per kelas.  

- **Preprocessing (PCV)**  
  - Resize gambar (misal 224×224 px).  
  - Normalisasi piksel (0–1).  
  - Augmentasi data (rotasi, flip, pencahayaan).  
  - (Opsional) Segmentasi citra untuk crop hanya buah jagung.  

- **Output**: Dataset siap latih dalam folder `grade_a/`, `grade_b/`, `grade_c/`.

### Tahap 3 – Training Model AI
- **Pemodelan AI (Sistem Kecerdasan)**  
  - Pilih arsitektur CNN sederhana atau Transfer Learning (ResNet50, MobileNet).  
  - Latih model dengan dataset jagung.  
  - Evaluasi dengan confusion matrix, precision, recall, F1-score.  

- **Optimisasi Model**  
  - Hyperparameter tuning.  
  - Simpan model ke format `.h5` dan `.tflite`.  

- **Output**: Model AI siap pakai untuk klasifikasi jagung Grade A, B, C.

### Tahap 4 – Implementasi Klasifikasi Real-Time
- **Program Real-Time Classification**  
  - Input kamera/webcam.  
  - Jalankan inferensi model secara langsung.  
  - Tampilkan hasil klasifikasi di layar.  

- **Pengujian**  
  - Uji dengan buah jagung nyata.  
  - Catat akurasi real-time.  

- **Output**: Program real-time yang dapat mendeteksi dan menampilkan Grade jagung.

### Tahap 5 – Integrasi IoT
- **Komunikasi IoT**  
  - ESP32/ESP8266 untuk mengirim hasil klasifikasi ke server/cloud.  
  - Alternatif: Python script publish ke MQTT broker/Firebase.  

- **Dashboard Monitoring**  
  - Web dashboard (HTML, CSS, JS).  
  - Menampilkan jumlah jagung per grade (A, B, C).  
  - Grafik tren batch.  

- **Output**: Dashboard real-time untuk memonitor hasil sortir jagung.

### Tahap 6 – Mekanisme Sortir Fisik (Opsional)
- **Kontrol Mekanis**  
  - Servo/motor untuk memisahkan jagung sesuai Grade.  
  - Integrasi dengan ESP32 untuk mengarahkan jagung ke wadah A, B, C.  

- **Pengujian Sistem Lengkap**  
  - Uji coba dengan jagung bergerak di conveyor/wadah.  

- **Output**: Prototipe mesin sortir otomatis (jika diwajibkan).
