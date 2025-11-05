import pandas as pd
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

# =========================================================
# 1. Baca Data Fitur
# =========================================================
df = pd.read_csv(r"E:\DragonEye\dataset\features.csv")

# Normalisasi otomatis setiap fitur ke skala [0, 1]
def normalize(series):
    if series.max() == series.min():
        return np.zeros_like(series)
    return (series - series.min()) / (series.max() - series.min())

df['area_norm'] = normalize(df['area'])
df['weight_norm'] = normalize(df['weight_est'])

# =========================================================
# 2. Definisi Variabel Fuzzy
# =========================================================
ukuran = ctrl.Antecedent(np.arange(0, 1.01, 0.01), 'ukuran')
berat = ctrl.Antecedent(np.arange(0, 1.01, 0.01), 'berat')
grade_out = ctrl.Consequent(np.arange(0, 101, 1), 'grade_out')

# =========================================================
# 3. Fuzzifikasi (Membership Functions)
# =========================================================
# Ukuran
ukuran['kecil'] = fuzz.trimf(ukuran.universe, [0.0, 0.0, 0.4])
ukuran['sedang'] = fuzz.trimf(ukuran.universe, [0.3, 0.5, 0.7])
ukuran['besar'] = fuzz.trimf(ukuran.universe, [0.6, 1.0, 1.0])

# Berat
berat['rendah'] = fuzz.trimf(berat.universe, [0.0, 0.0, 0.4])
berat['sedang'] = fuzz.trimf(berat.universe, [0.3, 0.5, 0.7])
berat['tinggi'] = fuzz.trimf(berat.universe, [0.6, 1.0, 1.0])

# Grade (Output)
grade_out['C'] = fuzz.trimf(grade_out.universe, [0, 0, 40])
grade_out['B'] = fuzz.trimf(grade_out.universe, [30, 50, 70])
grade_out['A'] = fuzz.trimf(grade_out.universe, [60, 100, 100])

# =========================================================
# 4. Aturan Fuzzy (Mamdani)
# =========================================================
rules = [
    ctrl.Rule(ukuran['besar'] & berat['tinggi'], grade_out['A']),
    ctrl.Rule(ukuran['sedang'] & berat['sedang'], grade_out['B']),
    ctrl.Rule(ukuran['kecil'] & berat['rendah'], grade_out['C']),
]

grading_ctrl = ctrl.ControlSystem(rules)

# =========================================================
# 5. Proses Grading
# =========================================================
grades = []

for _, row in df.iterrows():
    # Skip jika ada NaN
    if any(np.isnan([row['area_norm'], row['weight_norm']])):
        grades.append((np.nan, 'C'))
        continue

    grading = ctrl.ControlSystemSimulation(grading_ctrl)
    grading.input['ukuran'] = float(row['area_norm'])
    grading.input['berat'] = float(row['weight_norm'])

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
# 6. Simpan Hasil Grading
# =========================================================
output_path = r"E:\DragonEye\dataset\graded_features.csv"
df.to_csv(output_path, index=False, encoding='utf-8')

print("Grading selesai! Hasil disimpan ke graded_features.csv")

# =========================================================
# 7. Ringkasan
# =========================================================
print(df[['filename', 'area', 'weight_est', 'grade_label']].head(10))
print(df['grade_label'].value_counts())
