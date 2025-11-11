import pandas as pd
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

# =========================================================
# 1️⃣ Baca Data Fitur
# =========================================================
df = pd.read_csv(r"E:\DragonEye\dataset\features.csv")

if 'texture_score' not in df.columns:
    raise ValueError("Kolom 'texture_score' tidak ditemukan di features.csv.")

# =========================================================
# 2️⃣ Normalisasi fitur
# =========================================================
def normalize(series):
    s_min, s_max = series.min(), series.max()
    if s_max == s_min:
        return np.zeros_like(series)
    return np.clip((series - s_min) / (s_max - s_min), 0, 1)

def normalize_texture(series):
    eps = 1e-6
    log_norm = np.log1p(series - series.min() + eps)
    log_norm = (log_norm - log_norm.min()) / (log_norm.max() - log_norm.min())
    return np.clip(log_norm, 0, 1)

df['area_norm'] = normalize(df['area'])
df['weight_norm'] = normalize(df['weight_est'])
df['texture_norm'] = normalize_texture(df['texture_score'])

# =========================================================
# 3️⃣ Definisi variabel fuzzy
# =========================================================
ukuran = ctrl.Antecedent(np.arange(0, 1.01, 0.01), 'ukuran')
berat = ctrl.Antecedent(np.arange(0, 1.01, 0.01), 'berat')
tekstur = ctrl.Antecedent(np.arange(0, 1.01, 0.01), 'tekstur')
grade_out = ctrl.Consequent(np.arange(0, 101, 1), 'grade_out')

# =========================================================
# 4️⃣ Membership Function — versi lebih sensitif ke “A”
# =========================================================
ukuran['kecil'] = fuzz.trimf(ukuran.universe, [0.0, 0.0, 0.35])
ukuran['sedang'] = fuzz.trimf(ukuran.universe, [0.3, 0.55, 0.7])
ukuran['besar']  = fuzz.trimf(ukuran.universe, [0.6, 0.9, 1.0])

berat['rendah']  = fuzz.trimf(berat.universe, [0.0, 0.0, 0.35])
berat['sedang']  = fuzz.trimf(berat.universe, [0.3, 0.55, 0.7])
berat['tinggi']  = fuzz.trimf(berat.universe, [0.6, 0.9, 1.0])

tekstur['kasar'] = fuzz.trimf(tekstur.universe, [0.0, 0.0, 0.25])
tekstur['normal']= fuzz.trimf(tekstur.universe, [0.2, 0.45, 0.7])
tekstur['halus'] = fuzz.trimf(tekstur.universe, [0.4, 0.7, 1.0])

grade_out['C'] = fuzz.trimf(grade_out.universe, [0, 0, 40])
grade_out['B'] = fuzz.trimf(grade_out.universe, [35, 55, 75])
grade_out['A'] = fuzz.trimf(grade_out.universe, [60, 100, 100])

# =========================================================
# 5️⃣ Aturan fuzzy — diperluas agar A lebih mudah muncul
# =========================================================
rules = [
    # --- Grade A ---
    ctrl.Rule(ukuran['besar'] & berat['tinggi'], grade_out['A']),
    ctrl.Rule(ukuran['sedang'] & berat['tinggi'], grade_out['A']),
    ctrl.Rule(ukuran['besar'] & tekstur['normal'], grade_out['A']),
    ctrl.Rule(berat['tinggi'] & tekstur['halus'], grade_out['A']),
    ctrl.Rule(ukuran['besar'] & tekstur['halus'], grade_out['A']),
    ctrl.Rule(ukuran['sedang'] & berat['sedang'] & tekstur['halus'], grade_out['A']),

    # --- Grade B ---
    ctrl.Rule(ukuran['sedang'] & berat['sedang'], grade_out['B']),
    ctrl.Rule(ukuran['besar'] & tekstur['kasar'], grade_out['B']),
    ctrl.Rule(ukuran['sedang'] & tekstur['normal'], grade_out['B']),
    ctrl.Rule(berat['rendah'] & tekstur['halus'], grade_out['B']),
    ctrl.Rule(ukuran['besar'] & berat['rendah'], grade_out['B']),
    ctrl.Rule(ukuran['kecil'] & berat['tinggi'], grade_out['B']),

    # --- Grade C ---
    ctrl.Rule(ukuran['kecil'] | berat['rendah'], grade_out['C']),
    ctrl.Rule(tekstur['kasar'], grade_out['C']),
]

grading_ctrl = ctrl.ControlSystem(rules)

# =========================================================
# 6️⃣ Proses grading
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

    if score >= 60:
        label = 'A'
    elif score >= 40:
        label = 'B'
    else:
        label = 'C'

    grades.append((score, label))

df['grade_score'] = [g[0] for g in grades]
df['grade_label'] = [g[1] for g in grades]

# =========================================================
# 7️⃣ Simpan & ringkasan
# =========================================================
output_path = r"E:\DragonEye\dataset\graded_features.csv"
df.to_csv(output_path, index=False, encoding='utf-8')

print("[OK] Grading selesai! Hasil disimpan ke graded_features.csv")
print("\n Contoh hasil grading:")
print(df[['filename', 'area', 'weight_est', 'texture_score', 'grade_label']].head(10))
print("\n Jumlah tiap grade:")
print(df['grade_label'].value_counts())
