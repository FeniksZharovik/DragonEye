import pandas as pd
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

# 1️⃣ Baca data fitur
df = pd.read_csv(r"E:\DragonEye\dataset\features.csv")

if 'hue_mean' not in df.columns:
    raise ValueError("Kolom 'hue_mean' tidak ditemukan di features.csv")

# 2️⃣ Normalisasi hue dan tekstur
def normalize(series):
    s_min, s_max = series.min(), series.max()
    if s_max == s_min:
        return np.zeros_like(series)
    return np.clip((series - s_min) / (s_max - s_min), 0, 1)

df['hue_norm'] = normalize(df['hue_mean'])
df['texture_norm'] = normalize(df['texture_score'])

# 3️⃣ Definisi variabel fuzzy
warna = ctrl.Antecedent(np.arange(0, 1.01, 0.01), 'warna')
tekstur = ctrl.Antecedent(np.arange(0, 1.01, 0.01), 'tekstur')
kondisi_out = ctrl.Consequent(np.arange(0, 101, 1), 'kondisi_out')

# 4️⃣ Membership function
warna['gelap'] = fuzz.trimf(warna.universe, [0.0, 0.0, 0.35])
warna['normal'] = fuzz.trimf(warna.universe, [0.3, 0.55, 0.75])
warna['cerah'] = fuzz.trimf(warna.universe, [0.7, 1.0, 1.0])

tekstur['kasar'] = fuzz.trimf(tekstur.universe, [0.0, 0.0, 0.3])
tekstur['normal'] = fuzz.trimf(tekstur.universe, [0.25, 0.55, 0.75])
tekstur['halus'] = fuzz.trimf(tekstur.universe, [0.6, 1.0, 1.0])

kondisi_out['rotten'] = fuzz.trimf(kondisi_out.universe, [0, 0, 40])
kondisi_out['defect'] = fuzz.trimf(kondisi_out.universe, [30, 55, 70])
kondisi_out['good'] = fuzz.trimf(kondisi_out.universe, [60, 100, 100])

# 5️⃣ Aturan fuzzy
rules = [
    ctrl.Rule(warna['cerah'] & tekstur['halus'], kondisi_out['good']),
    ctrl.Rule(warna['normal'] & tekstur['normal'], kondisi_out['good']),
    ctrl.Rule(warna['gelap'] & tekstur['halus'], kondisi_out['defect']),
    ctrl.Rule(warna['normal'] & tekstur['kasar'], kondisi_out['defect']),
    ctrl.Rule(warna['gelap'] & tekstur['kasar'], kondisi_out['rotten']),
]

kondisi_ctrl = ctrl.ControlSystem(rules)

# 6️⃣ Proses grading
kondisi_sim = []
for _, row in df.iterrows():
    sim = ctrl.ControlSystemSimulation(kondisi_ctrl)
    sim.input['warna'] = float(row['hue_norm'])
    sim.input['tekstur'] = float(row['texture_norm'])
    try:
        sim.compute()
        score = sim.output['kondisi_out']
    except Exception:
        score = 0

    if score >= 60:
        label = 'Good'
    elif score >= 40:
        label = 'Defect'
    else:
        label = 'Rotten'

    kondisi_sim.append((score, label))

df['texture_grade_score'] = [x[0] for x in kondisi_sim]
df['texture_grade_label'] = [x[1] for x in kondisi_sim]

# 7️⃣ Simpan hasil
output_path = r"E:\DragonEye\dataset\graded_texture_quality.csv"
df.to_csv(output_path, index=False, encoding='utf-8')

print("[OK] Grading tekstur & warna selesai!")
print(df[['filename', 'hue_mean', 'texture_score', 'texture_grade_label']].head(10))
print("\nJumlah tiap kategori:")
print(df['texture_grade_label'].value_counts())
