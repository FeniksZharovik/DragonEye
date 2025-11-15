# file: fuzzy_grading.py
import pandas as pd
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

# 1) baca data fitur
df = pd.read_csv(r"E:\DragonEye\dataset\features.csv")

required_cols = ['area_cm2', 'weight_est_g', 'texture_score']
for col in required_cols:
    if col not in df.columns:
        raise ValueError(f"Kolom '{col}' tidak ditemukan di features.csv.")

# 2) klasifikasi langsung berdasarkan berat (aturan yang kamu berikan)
def grade_by_weight(weight_g):
    if weight_g >= 350:
        return 'A'
    elif weight_g >= 250:
        return 'B'
    else:
        return 'C'

df['grade_by_weight'] = df['weight_est_g'].apply(grade_by_weight)

# 3) (opsional) buat fuzzy score sebagai second opinion
# normalisasi berbasis distribusi (gunakan percentiles untuk menghindari outlier)
def normalize_pct(series, low_pct=5, high_pct=95):
    lo = np.percentile(series, low_pct)
    hi = np.percentile(series, high_pct)
    if hi == lo:
        return np.clip((series - series.min()) / (series.max() - series.min() + 1e-9), 0, 1)
    return np.clip((series - lo) / (hi - lo), 0, 1)

df['area_norm'] = normalize_pct(df['area_cm2'])
df['weight_norm'] = normalize_pct(df['weight_est_g'])
df['texture_norm'] = normalize_pct(df['texture_score'])

# 4) buat fuzzy controller (informasional)
ukuran = ctrl.Antecedent(np.linspace(0,1,101), 'ukuran')
berat   = ctrl.Antecedent(np.linspace(0,1,101), 'berat')
tekstur = ctrl.Antecedent(np.linspace(0,1,101), 'tekstur')
out     = ctrl.Consequent(np.linspace(0,100,101), 'out')

ukuran['kecil'] = fuzz.trimf(ukuran.universe, [0.0, 0.0, 0.4])
ukuran['sedang'] = fuzz.trimf(ukuran.universe, [0.3, 0.55, 0.75])
ukuran['besar'] = fuzz.trimf(ukuran.universe, [0.6, 1.0, 1.0])

berat['rendah'] = fuzz.trimf(berat.universe, [0.0, 0.0, 0.4])
berat['sedang'] = fuzz.trimf(berat.universe, [0.3, 0.55, 0.75])
berat['tinggi'] = fuzz.trimf(berat.universe, [0.6, 1.0, 1.0])

tekstur['kasar'] = fuzz.trimf(tekstur.universe, [0.0, 0.0, 0.3])
tekstur['normal'] = fuzz.trimf(tekstur.universe, [0.2, 0.45, 0.7])
tekstur['halus'] = fuzz.trimf(tekstur.universe, [0.4, 0.7, 1.0])

out['C'] = fuzz.trimf(out.universe, [0,0,40])
out['B'] = fuzz.trimf(out.universe, [35,55,75])
out['A'] = fuzz.trimf(out.universe, [65,100,100])

rules = [
    ctrl.Rule(ukuran['besar'] & berat['tinggi'], out['A']),
    ctrl.Rule(berat['tinggi'] & tekstur['halus'], out['A']),
    ctrl.Rule(ukuran['sedang'] & berat['sedang'] & tekstur['halus'], out['A']),
    ctrl.Rule(ukuran['sedang'] & berat['sedang'], out['B']),
    ctrl.Rule(tekstur['kasar'] | berat['rendah'], out['C']),
]

ctrlsys = ctrl.ControlSystem(rules)
sim = ctrl.ControlSystemSimulation(ctrlsys)

fuzzy_scores = []
for _, row in df.iterrows():
    sim.input['ukuran'] = float(row['area_norm'])
    sim.input['berat'] = float(row['weight_norm'])
    sim.input['tekstur'] = float(row['texture_norm'])
    try:
        sim.compute()
        score = float(sim.output['out'])
    except Exception:
        score = 0.0
    fuzzy_scores.append(score)

df['fuzzy_score'] = fuzzy_scores

# 5) gabungkan: gunakan grade_by_weight sebagai label utama
df['grade_label'] = df['grade_by_weight']

# 6) simpan
output_path = r"E:\DragonEye\dataset\graded_features.csv"
df.to_csv(output_path, index=False, encoding='utf-8')

print("[OK] Grading (berat utama) selesai.")
print(df[['filename','area_cm2','weight_est_g','texture_score','grade_label']].head(10))
print("\nJumlah tiap grade:")
print(df['grade_label'].value_counts())
