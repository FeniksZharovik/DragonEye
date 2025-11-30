# camera controller
import numpy as np
from services.pcv.pipeline import process_image  # Menjaga agar proses PCV tetap berjalan
from services.grading_service import run_fuzzy_and_save  # Menggunakan fungsi grading
from services.mqtt_service import publish  # Fungsi untuk publish ke MQTT

# Fungsi untuk mengambil gambar dari file upload atau kamera
async def process_image_from_file(file):
    # Baca file yang di-upload
    img_bytes = await file.read()
    img_array = np.frombuffer(img_bytes, np.uint8)

    # Jalankan PCV untuk memproses gambar
    features = process_image(img_array)

    # Jalankan grading dengan fuzzy
    result, err = run_fuzzy_and_save(
        image_bgr=features,  # Gambar yang telah diproses
        filename="uploaded_image.jpg",  # Nama file (bisa disesuaikan)
        db=None  # Pastikan sesi database terhubung di tempat yang sesuai
    )

    if err:
        raise Exception(f"Grading failed: {err}")

    # Kirim hasil grade ke IoT (MQTT)
    publish(result["final_grade"])

    return result