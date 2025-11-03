import pandas as pd
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

# =========================================================
# 1. BACA DATA FITUR
# =========================================================
df = pd.read_csv(r"E:\DragonEye\dataset\features.csv")

# Normalisasi otomatis setiap fitur ke skala [0, 1]
def normalize(series):
    if series.max() == series.min():
        return np.zeros_like(series)
    return (series - series.min()) / (series.max() - series.min())

df['hue_norm'] = normalize(df['hue_mean'])
df['texture_norm'] = normalize(df['texture_contrast'])
df['area_norm'] = normalize(df['area'])

# =========================================================
# 2. DEFINISI VARIABEL FUZZY
# =========================================================
warna = ctrl.Antecedent(np.arange(0, 1.01, 0.01), 'warna')
tekstur = ctrl.Antecedent(np.arange(0, 1.01, 0.01), 'tekstur')
ukuran = ctrl.Antecedent(np.arange(0, 1.01, 0.01), 'ukuran')
grade_out = ctrl.Consequent(np.arange(0, 101, 1), 'grade_out')

# =========================================================
# 3. FUZZIFIKASI (Membership Functions)
# =========================================================
# Warna
warna['pucat'] = fuzz.trimf(warna.universe, [0.0, 0.0, 0.4])
warna['merah'] = fuzz.trimf(warna.universe, [0.3, 0.5, 0.7])
warna['merah_tua'] = fuzz.trimf(warna.universe, [0.6, 1.0, 1.0])

# Tekstur
tekstur['kasar'] = fuzz.trimf(tekstur.universe, [0.0, 0.0, 0.4])
tekstur['sedikit_cacat'] = fuzz.trimf(tekstur.universe, [0.3, 0.5, 0.7])
tekstur['halus'] = fuzz.trimf(tekstur.universe, [0.6, 1.0, 1.0])

# Ukuran
ukuran['kecil'] = fuzz.trimf(ukuran.universe, [0.0, 0.0, 0.4])
ukuran['sedang'] = fuzz.trimf(ukuran.universe, [0.3, 0.5, 0.7])
ukuran['besar'] = fuzz.trimf(ukuran.universe, [0.6, 1.0, 1.0])

# Grade (Output)
grade_out['C'] = fuzz.trimf(grade_out.universe, [0, 0, 40])
grade_out['B'] = fuzz.trimf(grade_out.universe, [30, 50, 70])
grade_out['A'] = fuzz.trimf(grade_out.universe, [60, 100, 100])

# =========================================================
# 4. ATURAN FUZZY (Mamdani)
# =========================================================
rules = [
    ctrl.Rule(warna['merah_tua'] & tekstur['halus'] & ukuran['besar'], grade_out['A']),
    ctrl.Rule(warna['merah'] & tekstur['sedikit_cacat'], grade_out['B']),
    ctrl.Rule(warna['pucat'] | tekstur['kasar'], grade_out['C']),
    ctrl.Rule(ukuran['kecil'], grade_out['C']),
    ctrl.Rule(ukuran['sedang'] & warna['merah_tua'], grade_out['B']),
    ctrl.Rule(warna['merah'] & tekstur['halus'] & ukuran['besar'], grade_out['A']),
]

grading_ctrl = ctrl.ControlSystem(rules)

# =========================================================
# 5. PROSES GRADING
# =========================================================
grades = []

for _, row in df.iterrows():
    # Skip jika ada NaN
    if any(np.isnan([row['hue_norm'], row['texture_norm'], row['area_norm']])):
        grades.append((np.nan, 'C'))
        continue

    # Reset sistem fuzzy tiap iterasi
    grading = ctrl.ControlSystemSimulation(grading_ctrl)
    grading.input['warna'] = float(row['hue_norm'])
    grading.input['tekstur'] = float(row['texture_norm'])
    grading.input['ukuran'] = float(row['area_norm'])

    try:
        grading.compute()
        score = grading.output['grade_out']
    except Exception:
        score = 0

    if score >= 70:
        label = 'A'
    elif score >= 45:
        label = 'B'
    else:
        label = 'C'

    grades.append((score, label))

df['grade_score'] = [g[0] for g in grades]
df['grade_label'] = [g[1] for g in grades]

# =========================================================
# 6. SIMPAN HASIL
# =========================================================
output_path = r"E:\DragonEye\dataset\graded_features.csv"
df.to_csv(output_path, index=False, encoding='utf-8')

print("Grading selesai! Hasil disimpan ke graded_features.csv")

# =========================================================
# 7. RINGKASAN
# =========================================================
print(df[['filename', 'hue_mean', 'texture_contrast', 'area', 'grade_label']].head(10))
print(df['grade_label'].value_counts())
