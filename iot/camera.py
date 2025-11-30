import cv2
import numpy as np
import os

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
# Loop Utama
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
    # SAVE → always replace
    # =========================
    if key == ord('s'):
        cv2.imwrite(SAVE_PATH, output)
        print("[INFO] Gambar disimpan & replace:", SAVE_PATH)

    if key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
