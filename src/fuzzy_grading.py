import pandas as pd
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

# 1) Baca data fitur
df = pd.read_csv(r"E:\DragonEye\dataset\features.csv")

required_cols = ['area_cm2', 'weight_est_g', 'texture_score', 'hue_mean']
for col in required_cols:
    if col not in df.columns:
        raise ValueError(f"Kolom '{col}' tidak ditemukan di features.csv.")

# 2) Klasifikasi langsung berdasarkan berat (aturan yang kamu berikan)
def grade_by_weight(weight_g):
    if weight_g >= 350:
        return 'A'
    elif weight_g >= 250:
        return 'B'
    else:
        return 'C'

df['grade_by_weight'] = df['weight_est_g'].apply(grade_by_weight)

# 3) Normalisasi berbasis distribusi (gunakan percentiles untuk menghindari outlier)
def normalize_pct(series, low_pct=5, high_pct=95):
    lo = np.percentile(series, low_pct)
    hi = np.percentile(series, high_pct)
    if hi == lo:
        return np.clip((series - series.min()) / (series.max() - series.min() + 1e-9), 0, 1)
    return np.clip((series - lo) / (hi - lo), 0, 1)

df['area_norm'] = normalize_pct(df['area_cm2'])
df['weight_norm'] = normalize_pct(df['weight_est_g'])
df['texture_norm'] = normalize_pct(df['texture_score'])
df['hue_norm'] = normalize_pct(df['hue_mean'])

# 4) Membuat fuzzy controller (untuk ukuran, berat, tekstur, dan warna)
ukuran = ctrl.Antecedent(np.linspace(0, 1, 101), 'ukuran')
berat = ctrl.Antecedent(np.linspace(0, 1, 101), 'berat')
tekstur = ctrl.Antecedent(np.linspace(0, 1, 101), 'tekstur')
warna = ctrl.Antecedent(np.linspace(0, 1, 101), 'warna')
kondisi = ctrl.Consequent(np.linspace(0, 100, 101), 'kondisi')

# Definisi fuzzy set
ukuran['kecil'] = fuzz.trimf(ukuran.universe, [0.0, 0.0, 0.4])
ukuran['sedang'] = fuzz.trimf(ukuran.universe, [0.3, 0.55, 0.75])
ukuran['besar'] = fuzz.trimf(ukuran.universe, [0.6, 1.0, 1.0])

berat['rendah'] = fuzz.trimf(berat.universe, [0.0, 0.0, 0.4])
berat['sedang'] = fuzz.trimf(berat.universe, [0.3, 0.55, 0.75])
berat['tinggi'] = fuzz.trimf(berat.universe, [0.6, 1.0, 1.0])

tekstur['kasar'] = fuzz.trimf(tekstur.universe, [0.0, 0.0, 0.3])
tekstur['normal'] = fuzz.trimf(tekstur.universe, [0.2, 0.45, 0.7])
tekstur['halus'] = fuzz.trimf(tekstur.universe, [0.4, 0.7, 1.0])

warna['gelap'] = fuzz.trimf(warna.universe, [0.0, 0.0, 0.4])
warna['normal'] = fuzz.trimf(warna.universe, [0.3, 0.55, 0.8])
warna['cerah'] = fuzz.trimf(warna.universe, [0.65, 1.0, 1.0])

kondisi['rotten'] = fuzz.trimf(kondisi.universe, [0, 0, 40])
kondisi['defect'] = fuzz.trimf(kondisi.universe, [35, 55, 75])
kondisi['good'] = fuzz.trimf(kondisi.universe, [65, 100, 100])

# 5) Definisikan aturan fuzzy untuk kombinasi ukuran, berat, tekstur, dan warna
rules = [
    ctrl.Rule(ukuran['besar'] & berat['tinggi'], kondisi['good']),
    ctrl.Rule(berat['tinggi'] & tekstur['halus'], kondisi['good']),
    ctrl.Rule(ukuran['sedang'] & berat['sedang'] & tekstur['halus'], kondisi['good']),
    ctrl.Rule(ukuran['sedang'] & berat['sedang'], kondisi['defect']),
    ctrl.Rule(tekstur['kasar'] | berat['rendah'], kondisi['rotten']),
    ctrl.Rule(warna['cerah'] & tekstur['halus'], kondisi['good']),
    ctrl.Rule(warna['normal'] & tekstur['halus'], kondisi['good']),
    ctrl.Rule(warna['normal'] & tekstur['normal'], kondisi['defect']),
    ctrl.Rule(warna['gelap'] & tekstur['kasar'], kondisi['rotten']),
]

ctrlsys = ctrl.ControlSystem(rules)
sim = ctrl.ControlSystemSimulation(ctrlsys)

# 6) Hitung skor fuzzy untuk setiap gambar dalam dataset
fuzzy_scores = []
for _, row in df.iterrows():
    sim.input['ukuran'] = float(row['area_norm'])
    sim.input['berat'] = float(row['weight_norm'])
    sim.input['tekstur'] = float(row['texture_norm'])
    sim.input['warna'] = float(row['hue_norm'])
    try:
        sim.compute()
        score = float(sim.output['kondisi'])
    except Exception:
        score = 0.0
    fuzzy_scores.append(score)

df['fuzzy_score'] = fuzzy_scores

# 7) Gabungkan grading berdasarkan berat dan kualitas fuzzy
def combine_grading(weight_grade, fuzzy_grade):
    return f"{weight_grade} {fuzzy_grade}"

# Tentukan fuzzy grading berdasarkan nilai output dari logika fuzzy
def get_fuzzy_label(score):
    if score >= 65:
        return 'good'
    elif score >= 40:
        return 'defect'
    else:
        return 'rotten'

df['fuzzy_grade_label'] = df['fuzzy_score'].apply(get_fuzzy_label)

# 8) Gabungkan grading berdasarkan berat dan fuzzy grade untuk label akhir
df['final_grade'] = df.apply(lambda row: combine_grading(row['grade_by_weight'], row['fuzzy_grade_label']), axis=1)

# 9) Simpan hasil ke CSV
output_path = r"E:\DragonEye\dataset\graded_features.csv"
df.to_csv(output_path, index=False, encoding='utf-8')

# 10) Tampilkan hasil
print("[OK] Grading selesai!")
print(df[['filename', 'area_cm2', 'weight_est_g', 'texture_score', 'final_grade']].head(10))
print("\nJumlah tiap grade:")
print(df['final_grade'].value_counts())
