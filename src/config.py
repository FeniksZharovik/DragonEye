import os

# Folder utama
BASE_DIR = r"D:\Programming\Clone Github\DargonFruit_Grading"
RAW_DATA_DIR = os.path.join(BASE_DIR, "raw_data")
OUTPUT_DIR = os.path.join(BASE_DIR, "dataset")
SEGMENTED_DIR = os.path.join(OUTPUT_DIR, "segmented")
FEATURE_CSV = os.path.join(OUTPUT_DIR, "features.csv")

# Pastikan folder output ada
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(SEGMENTED_DIR, exist_ok=True)
