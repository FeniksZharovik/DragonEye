import cv2
import numpy as np
import os
import sys

# =========================
# IMPORT MODEL & MQTT SENDER
# =========================
sys.path.append(r"E:\DragonEye\model")
sys.path.append(r"E:\DragonEye\iot")

from predict_single import predict_single_image
from mqtt_machine_bridge import send_grade   # ← Kirim grade via MQTT

TARGET_SIZE = 3060

# =========================
# Folder & Nama File Fix
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_DIR = os.path.join(BASE_DIR, "..", "data")
os.makedirs(SAVE_DIR, exist_ok=True)

SAVE_PATH = os.path.join(SAVE_DIR, "photo_latest.jpg")


# =========================
# Hilangkan bingkai hitam
# =========================
def remove_black_border(frame, threshold=15):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    mask = gray > threshold
    coords = np.column_stack(np.where(mask))

    if coords.size == 0:
        return frame

    y_min, x_min = coords.min(axis=0)
    y_max, x_max = coords.max(axis=0)

    cropped = frame[y_min:y_max, x_min:x_max]

    if cropped.size == 0:
        return frame

    return cropped


# =========================
# Cari kamera otomatis
# =========================
camera_index = -1
for i in range(5):
    cap_test = cv2.VideoCapture(i)
    if cap_test.isOpened():
        print("Kamera ditemukan pada index", i)
        camera_index = i
        cap_test.release()
        break

if camera_index == -1:
    print("Tidak ada kamera!")
    exit()

cap = cv2.VideoCapture(camera_index)


# =========================
# LOOP UTAMA
# =========================
while True:
    ret, frame = cap.read()
    if not ret:
        print("Frame tidak terbaca")
        break

    frame_clean = remove_black_border(frame)

    h, w = frame_clean.shape[:2]
    if h == 0 or w == 0:
        continue

    # Crop ke 1:1
    side = min(h, w)
    x1 = (w - side) // 2
    y1 = (h - side) // 2
    square = frame_clean[y1:y1+side, x1:x1+side]

    if square.size == 0:
        continue

    output = cv2.resize(square, (TARGET_SIZE, TARGET_SIZE))

    cv2.imshow("Camera 1:1 (3060x3060)", output)

    key = cv2.waitKey(1)

    # =========================
    # SAVE dan PROSES
    # =========================
    if key == ord('s'):
        cv2.imwrite(SAVE_PATH, output)
        print("[INFO] Gambar disimpan →", SAVE_PATH)

        # Proses gambar untuk grading
        TEMP_DIR = os.path.join(BASE_DIR, "temp")
        os.makedirs(TEMP_DIR, exist_ok=True)

        temp_path = os.path.join(TEMP_DIR, "temp_uploaded_image.jpg")
        cv2.imwrite(temp_path, output)

        print("\nMemproses gambar...")

        try:
            result, err = predict_single_image(temp_path)

            if err:
                print("[ERROR] Pipeline gagal:", err)
            else:
                print("\nHASIL ANALISIS GAMBAR")
                print("Prediksi Grade :", result["grade"])
                print("Akurasi Fuzzy  :", f"{result['score']:.1f}%")
                print("Panjang        :", f"{result['length']:.2f} cm")
                print("Diameter       :", f"{result['diameter']:.2f} cm")
                print("Berat Estimasi :", f"{result['weight']:.0f} g")
                print("Rasio L/D      :", f"{result['ratio']:.2f}")

                # =========================
                # Kirim via MQTT
                # =========================
                send_grade(result["grade"])

        except Exception as e:
            print("Terjadi kesalahan:", e)

    if key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
