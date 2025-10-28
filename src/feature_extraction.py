import cv2
import numpy as np
import os
from skimage.feature import local_binary_pattern
import matplotlib.pyplot as plt

# Folder Path
segmented_data_path = r'E:\DragonEye\dataset\segmented'  # Gantilah dengan jalur folder segmented
output_data_path = r'E:\DragonEye\dataset\features'  # Gantilah dengan jalur folder output untuk hasil fitur

# Fungsi untuk ekstraksi fitur warna (misalnya, histogram warna)
def extract_color_features(image):
    hist_r = cv2.calcHist([image], [0], None, [256], [0, 256])
    hist_g = cv2.calcHist([image], [1], None, [256], [0, 256])
    hist_b = cv2.calcHist([image], [2], None, [256], [0, 256])
    hist_r /= hist_r.sum()
    hist_g /= hist_g.sum()
    hist_b /= hist_b.sum()
    
    color_features = np.concatenate([hist_r.flatten(), hist_g.flatten(), hist_b.flatten()])
    return color_features

def extract_texture_features(image):
    gray_image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    radius = 1
    n_points = 8 * radius
    lbp = local_binary_pattern(gray_image, n_points, radius, method="uniform")
    lbp_hist, _ = np.histogram(lbp.ravel(), bins=np.arange(0, 11), range=(0, 10))
    lbp_hist = lbp_hist.astype("float")
    lbp_hist /= lbp_hist.sum()
    lbp_image = np.uint8(lbp * 255 / (n_points))
    return lbp_hist.flatten(), lbp_image

def extract_size_features(image):
    gray_image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    _, thresh = cv2.threshold(gray_image, 127, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    areas = [cv2.contourArea(c) for c in contours]
    size_features = np.array(areas)
    contour_image = np.zeros_like(image)
    cv2.drawContours(contour_image, contours, -1, (0, 255, 0), 2)
    return size_features, contour_image

def extract_all_features():
    features = []
    for root, dirs, files in os.walk(segmented_data_path):
        for filename in files:
            if filename.endswith(('.jpg', '.png', '.jpeg')):
                image_path = os.path.join(root, filename)
                print(f"Extracting features from {filename}...")
                image = cv2.imread(image_path)
                if image is None:
                    print(f"Warning: {filename} could not be read!")
                    continue
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                color_features = extract_color_features(image_rgb)
                texture_features, lbp_image = extract_texture_features(image_rgb)
                size_features, contour_image = extract_size_features(image_rgb)
                all_features = np.concatenate([color_features, texture_features, size_features])
                features.append(all_features)

                # Menentukan folder berdasarkan kelas atau nama file
                class_folder = os.path.basename(root)  # Nama folder sebagai kelas
                class_output_path = os.path.join(output_data_path, class_folder)
                if not os.path.exists(class_output_path):
                    os.makedirs(class_output_path)

                lbp_output_path = os.path.join(class_output_path, f"lbp_{filename}")
                contour_output_path = os.path.join(class_output_path, f"contour_{filename}")

                cv2.imwrite(lbp_output_path, lbp_image)
                cv2.imwrite(contour_output_path, contour_image)
                print(f"Saved visualizations for {filename} at {lbp_output_path} and {contour_output_path}")
    
    return np.array(features)

features = extract_all_features()
print(f"Extracted features: {features.shape}")
