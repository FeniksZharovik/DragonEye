import pandas as pd

file_path = r"E:\DragonEye\dataset\graded_features.csv"
df = pd.read_csv(file_path)

print("Kolom yang ada:", df.columns)

def assign_label(filename):
    first_letter = str(filename)[0].upper()
    
    grade_map = {
        'A': 'A',
        'B': 'B',
        'C': 'C'
    }

    return grade_map.get(first_letter, "Unknown")

df['label_asli'] = df['filename'].apply(assign_label)

df.to_csv(file_path, index=False, encoding='utf-8')

print(f"[INFO] Kolom 'label_asli' berhasil diperbarui dan disimpan ke {file_path}")
