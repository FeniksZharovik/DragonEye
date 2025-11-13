import pandas as pd
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

# =========================================================
# 1️⃣ Baca Data Fitur
# =========================================================
df = pd.read_csv(r"E:\DragonEye\dataset\features.csv")

required_cols = ['area_cm2', 'weight_est_g', 'texture_score']
for col in required_cols:
    if col not in df.columns:
        raise ValueError(f"Kolom '{col}' tidak ditemukan di features.csv.")

# =========================================================
# 2️⃣ Normalisasi fitur (berdasarkan data fisik nyata)
# =========================================================
# Asumsi dari hasil pengukuran:
# Berat nyata buah naga: 150–550 g
# Luas proyeksi buah naga: 50–200 cm²
# Tekstur: 0–0.05 (dari hasil GLCM)
def normalize(series, min_val, max_val):
    return np.clip((series - min_val) / (max_val - min_val), 0, 1)

df['area_norm'] = normalize(df['area_cm2'], 50, 200)
df['weight_norm'] = normalize(df['weight_est_g'], 150, 550)
df['texture_norm'] = normalize(df['texture_score'], 0.0, 0.05)

# =========================================================
# 3️⃣ Definisi variabel fuzzy (berdasarkan skala 0–1)
# =========================================================
ukuran = ctrl.Antecedent(np.arange(0, 1.01, 0.01), 'ukuran')
berat = ctrl.Antecedent(np.arange(0, 1.01, 0.01), 'berat')
tekstur = ctrl.Antecedent(np.arange(0, 1.01, 0.01), 'tekstur')
grade_out = ctrl.Consequent(np.arange(0, 101, 1), 'grade_out')

# =========================================================
# 4️⃣ Membership Function (disesuaikan secara empiris)
# =========================================================
ukuran['kecil'] = fuzz.trimf(ukuran.universe, [0.0, 0.0, 0.35])
ukuran['sedang'] = fuzz.trimf(ukuran.universe, [0.3, 0.55, 0.75])
ukuran['besar']  = fuzz.trimf(ukuran.universe, [0.6, 1.0, 1.0])

berat['rendah']  = fuzz.trimf(berat.universe, [0.0, 0.0, 0.35])
berat['sedang']  = fuzz.trimf(berat.universe, [0.3, 0.55, 0.75])
berat['tinggi']  = fuzz.trimf(berat.universe, [0.6, 1.0, 1.0])

tekstur['kasar'] = fuzz.trimf(tekstur.universe, [0.0, 0.0, 0.25])
tekstur['normal'] = fuzz.trimf(tekstur.universe, [0.2, 0.45, 0.7])
tekstur['halus']  = fuzz.trimf(tekstur.universe, [0.4, 0.7, 1.0])

grade_out['C'] = fuzz.trimf(grade_out.universe, [0, 0, 40])
grade_out['B'] = fuzz.trimf(grade_out.universe, [35, 55, 75])
grade_out['A'] = fuzz.trimf(grade_out.universe, [65, 100, 100])

# =========================================================
# 5️⃣ Aturan fuzzy (berdasarkan korelasi fisik)
# =========================================================
rules = [
    # Grade A — besar, berat, halus
    ctrl.Rule(ukuran['besar'] & berat['tinggi'], grade_out['A']),
    ctrl.Rule(ukuran['sedang'] & berat['tinggi'], grade_out['A']),
    ctrl.Rule(ukuran['besar'] & tekstur['normal'], grade_out['A']),
    ctrl.Rule(berat['tinggi'] & tekstur['halus'], grade_out['A']),
    ctrl.Rule(ukuran['besar'] & tekstur['halus'], grade_out['A']),

    # Grade B — sedang, kombinasi sedang/normal
    ctrl.Rule(ukuran['sedang'] & berat['sedang'], grade_out['B']),
    ctrl.Rule(ukuran['besar'] & tekstur['kasar'], grade_out['B']),
    ctrl.Rule(ukuran['sedang'] & tekstur['normal'], grade_out['B']),
    ctrl.Rule(berat['rendah'] & tekstur['halus'], grade_out['B']),
    ctrl.Rule(ukuran['besar'] & berat['rendah'], grade_out['B']),
    ctrl.Rule(ukuran['kecil'] & berat['tinggi'], grade_out['B']),

    # Grade C — kecil, ringan, kasar
    ctrl.Rule(ukuran['kecil'] | berat['rendah'], grade_out['C']),
    ctrl.Rule(tekstur['kasar'], grade_out['C']),
]

grading_ctrl = ctrl.ControlSystem(rules)

# =========================================================
# 6️⃣ Proses grading fuzzy
# =========================================================
grades = []
for _, row in df.iterrows():
    grading = ctrl.ControlSystemSimulation(grading_ctrl)
    grading.input['ukuran'] = float(row['area_norm'])
    grading.input['berat'] = float(row['weight_norm'])
    grading.input['tekstur'] = float(row['texture_norm'])
    try:
        grading.compute()
        score = grading.output['grade_out']
    except Exception:
        score = 0

    if score >= 65:
        label = 'A'
    elif score >= 40:
        label = 'B'
    else:
        label = 'C'
    grades.append((score, label))

df['grade_score'] = [x[0] for x in grades]
df['grade_label'] = [x[1] for x in grades]

# =========================================================
# 7️⃣ Simpan & tampilkan ringkasan
# =========================================================
output_path = r"E:\DragonEye\dataset\graded_features.csv"
df.to_csv(output_path, index=False, encoding='utf-8')

print("[OK] Grading ukuran & berat selesai!")
print(df[['filename', 'area_cm2', 'weight_est_g', 'texture_score', 'grade_label']].head(10))
print("\nJumlah tiap grade:")
print(df['grade_label'].value_counts())
