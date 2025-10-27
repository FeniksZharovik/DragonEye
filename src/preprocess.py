import cv2
import os
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from skimage import exposure

def preprocess_image(image_path, output_path):
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
    # Mengambil semua gambar dalam folder
    image_paths = []
    for root, dirs, files in os.walk(input_folder):
        for file in files:
            if file.endswith(('.png', '.jpg', '.jpeg')):  # Menyaring format gambar
                image_paths.append(os.path.join(root, file))
    return image_paths

def grading_dragonfruit(image_path):
    # Membaca citra
    image = cv2.imread(image_path)
    
    # Analisis Warna Kulit (misalnya, mendeteksi warna merah dari kulit buah naga)
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower_red = np.array([0, 50, 50])
    upper_red = np.array([10, 255, 255])
    red_mask = cv2.inRange(hsv_image, lower_red, upper_red)
    
    # Menampilkan hasil segmentasi warna merah (kulit buah naga)
    red_segmented = cv2.bitwise_and(image, image, mask=red_mask)
    
    # Analisis Tekstur (gunakan metode seperti LBP atau GLCM untuk deteksi tekstur)
    # Di sini kita menggunakan perhitungan histogram sebagai contoh
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

def process_all_images():
    # Direktori input dan output
    input_folder = r'E:\DragonEye\raw_data'
    output_folder = r'E:\DragonEye\dataset\Processed'
    
    # Membuat folder output jika belum ada
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Mendapatkan semua gambar
    image_paths = get_image_paths(input_folder)
    
    for image_path in image_paths:
        # Proses Preprocessing
        processed_image = preprocess_image(image_path, output_folder)
        print(f"Preprocessing completed for {os.path.basename(image_path)}")
        
        # Grading Buah Naga
        grade, red_segmented, hist = grading_dragonfruit(processed_image)
        print(f"Grading for {os.path.basename(image_path)}: {grade}")
        
        # Menampilkan hasil grading dan segmentasi
        plt.figure(figsize=(10,5))
        plt.subplot(1, 3, 1)
        plt.imshow(cv2.cvtColor(red_segmented, cv2.COLOR_BGR2RGB))
        plt.title(f"Red Segmentation of {os.path.basename(image_path)}")
        
        plt.subplot(1, 3, 2)
        plt.plot(hist)
        plt.title("Texture Histogram")
        
        plt.subplot(1, 3, 3)
        plt.imshow(cv2.cvtColor(cv2.imread(image_path), cv2.COLOR_BGR2RGB))
        plt.title(f"Original Image {os.path.basename(image_path)}")
        
        plt.show()

if __name__ == "__main__":
    process_all_images()
