import cv2
import os
import numpy as np
import pandas as pd
import json
from skimage import exposure
from datetime import datetime
from tqdm import tqdm  # Untuk menampilkan progres di terminal dengan satu baris

def preprocess_image(image_path, output_path):
    """
    Preprocess the image by applying denoising, normalization, and histogram equalization.
    """
    # Membaca citra
    image = cv2.imread(image_path)
    
    # 1. Denoising (menggunakan Gaussian Blur untuk mengurangi noise)
    denoised_image = cv2.GaussianBlur(image, (5, 5), 0)
    
    # 2. Normalisasi (mengubah ke range [0, 1])
    norm_image = cv2.normalize(denoised_image, None, 0, 1, cv2.NORM_MINMAX)
    
    # 3. Peningkatan kontras dengan Histogram Equalization
    # Mengonversi citra ke grayscale untuk pengolahan
    gray_image = cv2.cvtColor(norm_image, cv2.COLOR_BGR2GRAY)
    enhanced_image = exposure.equalize_hist(gray_image)
    
    # Menyimpan hasil preprocessing
    filename = os.path.basename(image_path)
    output_file = os.path.join(output_path, f"processed_{filename}")
    cv2.imwrite(output_file, enhanced_image * 255)  # Mengalikan dengan 255 untuk mengembalikan ke skala [0, 255]
    return output_file

def get_image_paths(input_folder):
    """
    Mendapatkan semua gambar dalam folder dan sub-foldernya.
    """
    image_paths = []
    for root, dirs, files in os.walk(input_folder):
        for file in files:
            if file.endswith(('.png', '.jpg', '.jpeg')):  # Menyaring format gambar
                image_paths.append(os.path.join(root, file))
    return image_paths

def grading_dragonfruit(image_path):
    """
    Menilai kualitas kulit buah naga berdasarkan warna dan tekstur.
    """
    # Membaca citra
    image = cv2.imread(image_path)
    
    # Analisis Warna Kulit (misalnya, mendeteksi warna merah dari kulit buah naga)
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower_red = np.array([0, 50, 50])
    upper_red = np.array([10, 255, 255])
    red_mask = cv2.inRange(hsv_image, lower_red, upper_red)
    
    # Menyimpan hasil segmentasi warna merah
    red_segmented = cv2.bitwise_and(image, image, mask=red_mask)
    
    # Analisis Tekstur (gunakan metode seperti LBP atau GLCM untuk deteksi tekstur)
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    hist = cv2.calcHist([gray_image], [0], None, [256], [0, 256])
    
    # Menentukan apakah kondisi kulit baik berdasarkan analisis warna dan tekstur
    color_condition = np.sum(red_mask) / (image.shape[0] * image.shape[1])  # Persentase warna merah
    texture_condition = np.std(hist)  # Menggunakan standar deviasi histogram sebagai indikator tekstur
    
    # Mengembalikan hasil grading
    if color_condition > 0.2 and texture_condition < 50:
        grade = "Good"
    else:
        grade = "Poor"
    
    return grade, red_segmented, hist

def process_all_images(input_folder, output_folder):
    """
    Proses seluruh gambar dalam folder dan simpan hasilnya.
    """
    # Membuat folder output jika belum ada
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    metadata = []
    class_folders = os.listdir(input_folder)
    
    # Menyusuri semua folder dalam raw_data (folder kelas)
    for class_folder in class_folders:
        class_folder_path = os.path.join(input_folder, class_folder)
        if os.path.isdir(class_folder_path):
            class_output_folder = os.path.join(output_folder, class_folder)
            if not os.path.exists(class_output_folder):
                os.makedirs(class_output_folder)
            
            # Mendapatkan semua gambar dalam sub-folder kelas
            image_paths = get_image_paths(class_folder_path)
            
            # Inisialisasi tqdm untuk menampilkan progres di satu baris
            with tqdm(total=len(image_paths), desc=f"Processing {class_folder}", dynamic_ncols=True, ncols=100, leave=True) as pbar:
                for image_path in image_paths:
                    # Proses Preprocessing
                    processed_image = preprocess_image(image_path, class_output_folder)
                    
                    # Grading Buah Naga
                    grade, red_segmented, hist = grading_dragonfruit(processed_image)
                    
                    # Menyimpan metadata untuk CSV dan JSON
                    metadata.append({
                        "image": os.path.basename(image_path),
                        "class": class_folder,
                        "grade": grade,
                        "color_condition": np.sum(red_segmented),
                        "texture_condition": np.std(hist)
                    })
                    
                    # Update progres pada satu baris
                    pbar.update(1)

    # Simpan metadata ke CSV dan JSON
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    metadata_df = pd.DataFrame(metadata)
    metadata_file = f"dataset/metadata_{timestamp}.csv"
    metadata_df.to_csv(metadata_file, index=False)
    
    summary = {
        "total_images": len(metadata),
        "processed_images": len(metadata),
        "timestamp": timestamp
    }
    summary_file = f"dataset/summary_{timestamp}.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=4)
    
    print(f"[{timestamp}] INFO: Saved metadata {metadata_file} and summary {summary_file}")
    print(f"[{timestamp}] INFO: Processing complete.")

if __name__ == "__main__":
    input_folder = r'E:\DragonEye\raw_data'
    output_folder = r'E:\DragonEye\dataset\Processed'
    process_all_images(input_folder, output_folder)
