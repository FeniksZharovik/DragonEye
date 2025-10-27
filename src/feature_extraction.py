import cv2
import numpy as np
import os

# Folder Path
processed_data_path = r'E:\DragonEye\dataset\Processed'

# Fungsi untuk ekstraksi fitur warna (misalnya, histogram warna)
def extract_color_features(image):
    # Menghitung histogram warna untuk citra RGB
    hist_r = cv2.calcHist([image], [0], None, [256], [0, 256])
    hist_g = cv2.calcHist([image], [1], None, [256], [0, 256])
    hist_b = cv2.calcHist([image], [2], None, [256], [0, 256])

    # Normalisasi histogram untuk memudahkan perbandingan
    hist_r /= hist_r.sum()
    hist_g /= hist_g.sum()
    hist_b /= hist_b.sum()
    
    # Fitur warna adalah kombinasi dari histogram R, G, B
    color_features = np.concatenate([hist_r.flatten(), hist_g.flatten(), hist_b.flatten()])
    return color_features

# Fungsi untuk ekstraksi fitur tekstur (menggunakan LBP atau GLCM)
def extract_texture_features(image):
    # Convert image to grayscale
    gray_image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    
    # Menghitung Local Binary Pattern (LBP) untuk tekstur
    radius = 1
    n_points = 8 * radius
    lbp = cv2.localBinaryPattern(gray_image, n_points, radius, method="uniform")
    
    # Menghitung histogram LBP
    lbp_hist = cv2.calcHist([lbp], [0], None, [256], [0, 256])
    lbp_hist /= lbp_hist.sum()  # Normalisasi
    
    return lbp_hist.flatten()

# Fungsi untuk ekstraksi fitur ukuran (misalnya, area dari objek yang terdeteksi)
def extract_size_features(image):
    # Menggunakan threshold untuk memisahkan objek dari latar belakang
    gray_image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    _, thresh = cv2.threshold(gray_image, 127, 255, cv2.THRESH_BINARY)
    
    # Menemukan kontur pada citra threshold
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Menghitung area dari semua kontur
    areas = [cv2.contourArea(c) for c in contours]
    size_features = np.array(areas)
    
    return size_features

# Fungsi utama untuk ekstraksi semua fitur
def extract_all_features():
    features = []
    for filename in os.listdir(processed_data_path):
        if filename.endswith(('.jpg', '.png', '.jpeg')):
            image_path = os.path.join(processed_data_path, filename)
            print(f"Extracting features from {filename}...")
            image = cv2.imread(image_path)
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Ekstraksi fitur
            color_features = extract_color_features(image_rgb)
            texture_features = extract_texture_features(image_rgb)
            size_features = extract_size_features(image_rgb)
            
            # Gabungkan semua fitur dalam satu array
            all_features = np.concatenate([color_features, texture_features, size_features])
            features.append(all_features)
    
    return np.array(features)

# Memulai ekstraksi fitur
features = extract_all_features()
print(f"Extracted features: {features.shape}")
