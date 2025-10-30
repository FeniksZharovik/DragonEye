import cv2
import os
import numpy as np
from tqdm import tqdm
from datetime import datetime

def preprocess_image(image_path, output_path, target_size=(224, 224)):
    """
    Preprocess image untuk EfficientNetB0 tanpa stretching kontras apapun.
    
    Tahapan:
    1. Membaca citra dari disk
    2. Konversi warna dari BGR → RGB
    3. Resize ke 224x224 (geometric stretching saja)
    4. Simpan hasilnya sebagai .jpg tanpa normalisasi preprocess_input
       (normalisasi dilakukan nanti di tahap training)
    
    Parameters:
        image_path (str): path ke gambar asli
        output_path (str): folder tujuan hasil preprocessing
        target_size (tuple): ukuran citra target (default: 224x224)
    """
    # Membaca citra
    image = cv2.imread(image_path)
    if image is None:
        print(f"[WARNING] Gagal membaca {image_path}")
        return None

    # Konversi BGR ke RGB (EfficientNet dilatih dengan RGB)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Resize (geometric stretching ke ukuran input model)
    image = cv2.resize(image, target_size, interpolation=cv2.INTER_AREA)

    # Pastikan nilai piksel tetap valid [0, 255]
    image = np.clip(image, 0, 255).astype(np.uint8)

    # Simpan hasil preprocessing
    filename = os.path.basename(image_path)
    output_file = os.path.join(output_path, f"processed_{filename}")

    # Konversi kembali ke BGR sebelum disimpan agar warna tampil benar di viewer biasa
    image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    cv2.imwrite(output_file, image_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 95])

    return output_file


def get_image_paths(input_folder):
    """
    Mengambil semua path gambar dari folder (termasuk subfolder).
    """
    image_paths = []
    for root, _, files in os.walk(input_folder):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                image_paths.append(os.path.join(root, file))
    return image_paths


def process_all_images(input_folder, output_folder):
    """
    Proses seluruh gambar dalam folder input dan simpan hasilnya ke folder output.
    Tidak menggunakan teknik stretching kontras apapun.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    class_folders = os.listdir(input_folder)

    for class_folder in class_folders:
        class_folder_path = os.path.join(input_folder, class_folder)
        if os.path.isdir(class_folder_path):
            class_output_folder = os.path.join(output_folder, class_folder)
            os.makedirs(class_output_folder, exist_ok=True)

            image_paths = get_image_paths(class_folder_path)
            with tqdm(total=len(image_paths), desc=f"Processing {class_folder}", ncols=100) as pbar:
                for image_path in image_paths:
                    preprocess_image(image_path, class_output_folder)
                    pbar.update(1)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"[{timestamp}] ✅ Preprocessing selesai tanpa stretching. Hasil disimpan di '{output_folder}'.")


if __name__ == "__main__":
    input_folder = r"E:\DragonEye\raw_data"            # Folder input dataset mentah
    output_folder = r"E:\DragonEye\dataset\processed"  # Folder output hasil preprocessing
    process_all_images(input_folder, output_folder)
