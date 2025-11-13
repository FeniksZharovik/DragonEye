import pandas as pd
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

# =========================================================
# 1️⃣ Baca data fitur
# =========================================================
df = pd.read_csv(r"E:\DragonEye\dataset\features.csv")

required_cols = ['hue_mean', 'texture_score']
for col in required_cols:
    if col not in df.columns:
        raise ValueError(f"Kolom '{col}' tidak ditemukan di features.csv.")

# =========================================================
# 2️⃣ Normalisasi hue dan tekstur
# =========================================================
# Hue rata-rata dari cv2.cvtColor (HSV.H) biasanya 0–1 (setelah dibagi 180)
# Buah naga matang cenderung berada di hue 0.5–0.65 (merah keunguan)
def normalize_range(series, min_val, max_val):
    return np.clip((series - min_val) / (max_val - min_val), 0, 1)

df['hue_norm'] = normalize_range(df['hue_mean'], 0.45, 0.6)
df['texture_norm'] = normalize_range(df['texture_score'], 0.0, 0.03)

# =========================================================
# 3️⃣ Definisi variabel fuzzy
# =========================================================
warna = ctrl.Antecedent(np.arange(0, 1.01, 0.01), 'warna')
tekstur = ctrl.Antecedent(np.arange(0, 1.01, 0.01), 'tekstur')
kondisi_out = ctrl.Consequent(np.arange(0, 101, 1), 'kondisi_out')

# =========================================================
# 4️⃣ Membership Function — disesuaikan dengan karakter buah naga
# =========================================================
warna['gelap'] = fuzz.trimf(warna.universe, [0.0, 0.0, 0.4])
warna['normal'] = fuzz.trimf(warna.universe, [0.3, 0.55, 0.8])
warna['cerah'] = fuzz.trimf(warna.universe, [0.6, 1.0, 1.0])

tekstur['kasar'] = fuzz.trimf(tekstur.universe, [0.0, 0.0, 0.4])
tekstur['normal'] = fuzz.trimf(tekstur.universe, [0.3, 0.6, 0.85])
tekstur['halus'] = fuzz.trimf(tekstur.universe, [0.7, 1.0, 1.0])

kondisi_out['rotten'] = fuzz.trimf(kondisi_out.universe, [0, 0, 40])
kondisi_out['defect'] = fuzz.trimf(kondisi_out.universe, [35, 55, 70])
kondisi_out['good'] = fuzz.trimf(kondisi_out.universe, [65, 100, 100])

# =========================================================
# 5️⃣ Aturan fuzzy
# =========================================================
rules = [
    ctrl.Rule(warna['cerah'] & tekstur['halus'], kondisi_out['good']),
    ctrl.Rule(warna['normal'] & tekstur['halus'], kondisi_out['good']),
    ctrl.Rule(warna['normal'] & tekstur['normal'], kondisi_out['good']),
    ctrl.Rule(warna['normal'] & tekstur['kasar'], kondisi_out['defect']),
    ctrl.Rule(warna['gelap'] & tekstur['normal'], kondisi_out['defect']),
    ctrl.Rule(warna['gelap'] & tekstur['kasar'], kondisi_out['rotten']),
]

kondisi_ctrl = ctrl.ControlSystem(rules)

# =========================================================
# 6️⃣ Proses grading tekstur & warna
# =========================================================
kondisi_sim = []
for _, row in df.iterrows():
    sim = ctrl.ControlSystemSimulation(kondisi_ctrl)
    sim.input['warna'] = float(np.clip(row['hue_norm'], 0, 1))
    sim.input['tekstur'] = float(np.clip(row['texture_norm'], 0, 1))

    try:
        sim.compute()
        score = sim.output['kondisi_out']
    except Exception:
        score = 0

    if score >= 65:
        label = 'Good'
    elif score >= 40:
        label = 'Defect'
    else:
        label = 'Rotten'

    kondisi_sim.append((score, label))

df['texture_grade_score'] = [x[0] for x in kondisi_sim]
df['texture_grade_label'] = [x[1] for x in kondisi_sim]

# =========================================================
# 7️⃣ Simpan hasil
# =========================================================
output_path = r"E:\DragonEye\dataset\graded_texture_quality.csv"
df.to_csv(output_path, index=False, encoding='utf-8')

print("[OK] Grading tekstur & warna selesai!")
print(df[['filename', 'hue_mean', 'texture_score', 'texture_grade_label']].head(10))
print("\nJumlah tiap kategori:")
print(df['texture_grade_label'].value_counts())
