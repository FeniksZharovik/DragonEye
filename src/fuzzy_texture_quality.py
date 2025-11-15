# file: fuzzy_texture_quality.py
import pandas as pd
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

df = pd.read_csv(r"E:\DragonEye\dataset\features.csv")

required_cols = ['hue_mean', 'texture_score']
for col in required_cols:
    if col not in df.columns:
        raise ValueError(f"Kolom '{col}' tidak ditemukan di features.csv.")

# Normalisasi adaptif berdasarkan percentiles (mengurangi pengaruh outlier)
def normalize_pct(series, low_pct=5, high_pct=95):
    lo = np.percentile(series, low_pct)
    hi = np.percentile(series, high_pct)
    if hi == lo:
        return np.clip((series - series.min()) / (series.max() - series.min() + 1e-9), 0, 1)
    return np.clip((series - lo) / (hi - lo), 0, 1)

# hue_mean umumnya antara 0..1 — kita gunakan percentiles untuk menangkap sebaran nyata
df['hue_norm'] = normalize_pct(df['hue_mean'], 5, 95)
df['texture_norm'] = normalize_pct(df['texture_score'], 5, 95)

# fuzzy vars
warna = ctrl.Antecedent(np.linspace(0,1,101),'warna')
tekstur = ctrl.Antecedent(np.linspace(0,1,101),'tekstur')
kondisi = ctrl.Consequent(np.linspace(0,100,101),'kondisi')

warna['gelap'] = fuzz.trimf(warna.universe, [0.0, 0.0, 0.4])
warna['normal'] = fuzz.trimf(warna.universe, [0.3, 0.55, 0.8])
warna['cerah'] = fuzz.trimf(warna.universe, [0.65, 1.0, 1.0])

tekstur['kasar'] = fuzz.trimf(tekstur.universe, [0.0, 0.0, 0.4])
tekstur['normal'] = fuzz.trimf(tekstur.universe, [0.3, 0.55, 0.8])
tekstur['halus'] = fuzz.trimf(tekstur.universe, [0.65, 1.0, 1.0])

kondisi['rotten'] = fuzz.trimf(kondisi.universe, [0,0,40])
kondisi['defect'] = fuzz.trimf(kondisi.universe, [35,55,75])
kondisi['good'] = fuzz.trimf(kondisi.universe, [65,100,100])

rules = [
    ctrl.Rule(warna['cerah'] & tekstur['halus'], kondisi['good']),
    ctrl.Rule(warna['normal'] & tekstur['halus'], kondisi['good']),
    ctrl.Rule(warna['normal'] & tekstur['normal'], kondisi['good']),
    ctrl.Rule(warna['normal'] & tekstur['kasar'], kondisi['defect']),
    ctrl.Rule(warna['gelap'] & tekstur['normal'], kondisi['defect']),
    ctrl.Rule(warna['gelap'] & tekstur['kasar'], kondisi['rotten']),
]

ctrlsys = ctrl.ControlSystem(rules)
sim = ctrl.ControlSystemSimulation(ctrlsys)

labels = []
scores = []
for _, row in df.iterrows():
    sim.input['warna'] = float(np.clip(row['hue_norm'],0,1))
    sim.input['tekstur'] = float(np.clip(row['texture_norm'],0,1))
    try:
        sim.compute()
        sc = float(sim.output['kondisi'])
    except Exception:
        sc = 0.0
    scores.append(sc)
    if sc >= 65:
        labels.append('Good')
    elif sc >= 40:
        labels.append('Defect')
    else:
        labels.append('Rotten')

df['texture_grade_score'] = scores
df['texture_grade_label'] = labels

output_path = r"E:\DragonEye\dataset\graded_texture_quality.csv"
df.to_csv(output_path, index=False, encoding='utf-8')

print("[OK] Grading tekstur & warna selesai!")
print(df[['filename','hue_mean','texture_score','texture_grade_label']].head(10))
print("\nJumlah tiap kategori:")
print(df['texture_grade_label'].value_counts())
