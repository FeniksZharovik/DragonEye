import pandas as pd

# Path ke file CSV yang ingin diperbarui
file_path = r"E:\DragonEye\dataset\graded_features.csv"

# Baca data dari file CSV
df = pd.read_csv(file_path)

# Periksa kolom yang ada di DataFrame
print("Kolom yang ada dalam DataFrame:", df.columns)

# Menambahkan kolom 'label_asli' berdasarkan awalan nama file
# Logika: 'A_' -> 'A', 'B_' -> 'B', 'C_' -> 'C'
def assign_label(filename):
    if filename.startswith('A'):
        return 'A'
    elif filename.startswith('B'):
        return 'B'
    elif filename.startswith('C'):
        return 'C'
    else:
        return 'Unknown'  # Jika nilai tidak sesuai, kembalikan 'Unknown'

# Terapkan fungsi untuk menambahkan kolom 'label_asli' berdasarkan nama file
df['label_asli'] = df['filename'].apply(assign_label)

# Simpan DataFrame kembali ke file CSV
df.to_csv(file_path, index=False, encoding='utf-8')

print(f"[INFO] Kolom 'label_asli' berhasil ditambahkan dan file disimpan ke {file_path}")
