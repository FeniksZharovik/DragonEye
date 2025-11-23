import pandas as pd
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

# 1) Baca data fitur (HARUS sudah ada kolom berikut)
df = pd.read_csv(r"E:\DragonEye\dataset\features.csv")

required_cols = ['length_cm', 'diameter_cm', 'weight_est_g']
for col in required_cols:
    if col not in df.columns:
        raise ValueError(f"Kolom '{col}' tidak ditemukan di features.csv.")

# 2) Hitung rasio ukuran-bobot
df['ratio'] = df['weight_est_g'] / (df['length_cm'] * df['diameter_cm'] + 1e-9)

# 3) Normalisasi dengan percentile (lebih aman dari outlier)
def normalize(series, p_low=5, p_high=95):
    lo = np.percentile(series, p_low)
    hi = np.percentile(series, p_high)
    return np.clip((series - lo) / (hi - lo + 1e-9), 0, 1)

df['length_norm'] = normalize(df['length_cm'])
df['diameter_norm'] = normalize(df['diameter_cm'])
df['weight_norm'] = normalize(df['weight_est_g'])
df['ratio_norm']  = normalize(df['ratio'])

# 4) Buat fuzzy variables
length = ctrl.Antecedent(np.linspace(0,1,101), 'length')
diameter = ctrl.Antecedent(np.linspace(0,1,101), 'diameter')
weight = ctrl.Antecedent(np.linspace(0,1,101), 'weight')
ratio = ctrl.Antecedent(np.linspace(0,1,101), 'ratio')

grade = ctrl.Consequent(np.linspace(0,100,101), 'grade')

# Membership function
length['small']  = fuzz.trimf(length.universe, [0.0, 0.0, 0.4])
length['medium'] = fuzz.trimf(length.universe, [0.3, 0.55, 0.8])
length['large']  = fuzz.trimf(length.universe, [0.6, 1.0, 1.0])

diameter['small']  = fuzz.trimf(diameter.universe, [0.0, 0.0, 0.4])
diameter['medium'] = fuzz.trimf(diameter.universe, [0.3, 0.55, 0.8])
diameter['large']  = fuzz.trimf(diameter.universe, [0.6, 1.0, 1.0])

weight['low']   = fuzz.trimf(weight.universe, [0.0, 0.0, 0.4])
weight['mid']   = fuzz.trimf(weight.universe, [0.3, 0.55, 0.8])
weight['high']  = fuzz.trimf(weight.universe, [0.6, 1.0, 1.0])

ratio['poor']   = fuzz.trimf(ratio.universe, [0.0, 0.0, 0.4])
ratio['normal'] = fuzz.trimf(ratio.universe, [0.3, 0.55, 0.8])
ratio['good']   = fuzz.trimf(ratio.universe, [0.6, 1.0, 1.0])

grade['C'] = fuzz.trimf(grade.universe, [0, 0, 45])
grade['B'] = fuzz.trimf(grade.universe, [35, 60, 85])
grade['A'] = fuzz.trimf(grade.universe, [75, 100, 100])

# 5) Definisikan aturan fuzzy
rules = [
    ctrl.Rule(weight['high'] & diameter['large'], grade['A']),
    ctrl.Rule(weight['high'] & length['large'], grade['A']),
    ctrl.Rule(weight['mid'] & diameter['medium'], grade['B']),
    ctrl.Rule(ratio['good'], grade['A']),
    ctrl.Rule(ratio['normal'], grade['B']),
    ctrl.Rule(ratio['poor'] | weight['low'], grade['C']),
]

control_sys = ctrl.ControlSystem(rules)
sim = ctrl.ControlSystemSimulation(control_sys)

# 6) Hitung fuzzy score per baris data
fuzzy_scores = []

for _, row in df.iterrows():
    sim.input['length'] = float(row['length_norm'])
    sim.input['diameter'] = float(row['diameter_norm'])
    sim.input['weight'] = float(row['weight_norm'])
    sim.input['ratio'] = float(row['ratio_norm'])
    
    try:
        sim.compute()
        score = float(sim.output['grade'])
    except:
        score = 0.0
    
    fuzzy_scores.append(score)

df['fuzzy_score'] = fuzzy_scores

# 7) Konversi ke label final
def get_label(score):
    if score >= 70:
        return 'A'
    elif score >= 45:
        return 'B'
    else:
        return 'C'

df['final_grade'] = df['fuzzy_score'].apply(get_label)

# 8) Simpan hasil
output = r"E:\DragonEye\dataset\graded_features.csv"
df.to_csv(output, index=False, encoding='utf-8')

print("[OK] Fuzzy grading selesai!")
print(df[['length_cm', 'diameter_cm', 'weight_est_g', 'ratio', 'final_grade']].head())
print(df['final_grade'].value_counts())
