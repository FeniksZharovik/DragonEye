import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

# Fuzzy universe
length = ctrl.Antecedent(np.linspace(0,1,101), 'length')
diameter = ctrl.Antecedent(np.linspace(0,1,101), 'diameter')
weight = ctrl.Antecedent(np.linspace(0,1,101), 'weight')
ratio = ctrl.Antecedent(np.linspace(0,1,101), 'ratio')

grade = ctrl.Consequent(np.linspace(0,100,101), 'grade')

# Membership function sama seperti fuzzy_grading.py
length['small']  = fuzz.trimf(length.universe, [0,0,0.4])
length['medium'] = fuzz.trimf(length.universe, [0.3,0.55,0.8])
length['large']  = fuzz.trimf(length.universe, [0.6,1,1])

diameter['small']  = fuzz.trimf(diameter.universe, [0,0,0.4])
diameter['medium'] = fuzz.trimf(diameter.universe, [0.3,0.55,0.8])
diameter['large']  = fuzz.trimf(diameter.universe, [0.6,1,1])

weight['low']   = fuzz.trimf(weight.universe, [0,0,0.4])
weight['mid']   = fuzz.trimf(weight.universe, [0.3,0.55,0.8])
weight['high']  = fuzz.trimf(weight.universe, [0.6,1,1])

ratio['poor']   = fuzz.trimf(ratio.universe, [0,0,0.4])
ratio['normal'] = fuzz.trimf(ratio.universe, [0.3,0.55,0.8])
ratio['good']   = fuzz.trimf(ratio.universe, [0.6,1,1])

grade['C'] = fuzz.trimf(grade.universe, [0,0,45])
grade['B'] = fuzz.trimf(grade.universe, [35,60,85])
grade['A'] = fuzz.trimf(grade.universe, [75,100,100])

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

def normalize_value(x, min_val, max_val):
    return np.clip((x - min_val) / (max_val - min_val + 1e-9), 0, 1)

# ✨ fungsi fuzzy untuk 1 gambar
def fuzzy_grade_single(length_cm, diameter_cm, weight_g, ratio_val):

    # Normalisasi cepat berdasarkan asumsi dataset
    len_n = normalize_value(length_cm, 5, 18)
    dia_n = normalize_value(diameter_cm, 4, 12)
    w_n   = normalize_value(weight_g, 150, 650)
    ratio_n = normalize_value(ratio_val, 1.0, 1.8)

    sim.input['length'] = len_n
    sim.input['diameter'] = dia_n
    sim.input['weight'] = w_n
    sim.input['ratio'] = ratio_n
    
    sim.compute()
    score = float(sim.output['grade'])  # 0–100  (score tetap digunakan)

    # 🚨 DIUBAH: grade ditentukan oleh BERAT, bukan fuzzy score
    if weight_g > 350:
        grade = "A"
    elif 250 <= weight_g <= 350:
        grade = "B"
    else:
        grade = "C"

    return grade, score