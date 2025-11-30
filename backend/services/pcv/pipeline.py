# services/pcv/pipeline.py

import cv2
import numpy as np
from .preprocess import preprocess_image
from .segmentation import segment_image
from .feature_extract import extract_features


# ---------------------------------------------------
# Fungsi inti untuk proses citra (BGR → fitur lengkap)
# ---------------------------------------------------
def process_image_bgr(img_bgr):
    """
    Input:
        img_bgr = citra BGR OpenCV

    Output:
        dict:
            {
                "length_cm": float,
                "diameter_cm": float,
                "weight_est_g": float,
                "ratio": float,
                "segmented": segmented_img (HSV),
                "mask": mask
            }
    """

    # 1. Preprocessing
    hsv = preprocess_image(img_bgr)

    # 2. Segmentasi
    segmented, mask = segment_image(hsv)

    # 3. Ekstraksi fitur
    length_cm, diameter_cm, weight_est_g, ratio = extract_features(segmented, mask)

    return {
        "length_cm": length_cm,
        "diameter_cm": diameter_cm,
        "weight_est_g": weight_est_g,
        "ratio": ratio,
        "segmented": segmented,
        "mask": mask
    }


# ---------------------------------------------------
# Proses dari path file (digunakan oleh controller)
# ---------------------------------------------------
def process_image_path(path):
    img = cv2.imread(path)
    if img is None:
        raise ValueError(f"Gagal membaca file: {path}")

    return process_image_bgr(img)


# ---------------------------------------------------
# Proses dari upload bytes (FastAPI UploadFile)
# ---------------------------------------------------
def process_image_bytes(file_bytes):
    nparr = np.frombuffer(file_bytes, np.uint8)
    img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img_bgr is None:
        raise ValueError("Gambar tidak valid")

    return process_image_bgr(img_bgr)


# ---------------------------------------------------
# Wrapper kompatibilitas lama (untuk controller)
# ---------------------------------------------------
def process_image(img_source):
    """
    Wrapper untuk kompatibilitas
    img_source bisa: path, bytes, atau numpy array BGR
    """

    if isinstance(img_source, str):
        return process_image_path(img_source)

    elif isinstance(img_source, bytes):
        return process_image_bytes(img_source)

    elif isinstance(img_source, np.ndarray):
        return process_image_bgr(img_source)

    else:
        raise TypeError("Unsupported image source type")