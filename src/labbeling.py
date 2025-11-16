import pandas as pd

# Path ke file CSV yang ingin diperbarui
file_path = r"E:\DragonEye\dataset\graded_features.csv"

# Baca data
df = pd.read_csv(file_path)

print("Kolom yang ada:", df.columns)

# Fungsi label berdasarkan format file AG, AD, AR, BG, BD, BR, CG, CD, CR
def assign_label(filename):
    prefix = filename[:2].upper()   # contoh: 'AG', 'BD', 'CR'

    grade_map = {
        'A': 'grade A',
        'B': 'grade B',
        'C': 'grade C'
    }

    quality_map = {
        'G': 'good',
        'D': 'defect',
        'R': 'rotten'
    }

    if len(prefix) != 2:
        return "Unknown"

    grade_letter = prefix[0]
    quality_letter = prefix[1]

    grade = grade_map.get(grade_letter, "Unknown")
    quality = quality_map.get(quality_letter, "Unknown")

    return f"{grade} {quality}"

# Tambahkan kolom baru
df['label_asli'] = df['filename'].apply(assign_label)

# Simpan kembali
df.to_csv(file_path, index=False, encoding='utf-8')

print(f"[INFO] Kolom 'label_asli' berhasil diperbarui dan disimpan ke {file_path}")
