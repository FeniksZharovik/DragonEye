# file: services/fuzzy/rules.py
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

def build_fuzzy_controller():
    """
    Build and return a skfuzzy.control.ControlSystem configured with:
    - antecedents: length, diameter, weight, ratio (each 0..1)
    - consequent: score (0..100)
    The rules are designed so weight is primary factor, length/diameter/ratio are supportive.
    """

    # Antecedent universes
    length = ctrl.Antecedent(np.linspace(0, 1, 101), 'length')
    diameter = ctrl.Antecedent(np.linspace(0, 1, 101), 'diameter')
    weight = ctrl.Antecedent(np.linspace(0, 1, 101), 'weight')
    ratio = ctrl.Antecedent(np.linspace(0, 1, 101), 'ratio')

    # Consequent
    score = ctrl.Consequent(np.linspace(0, 100, 101), 'score')

    # Membership functions for length & diameter (small / medium / large)
    length['small']  = fuzz.trimf(length.universe, [0.0, 0.0, 0.4])
    length['medium'] = fuzz.trimf(length.universe, [0.3, 0.55, 0.75])
    length['large']  = fuzz.trimf(length.universe, [0.6, 1.0, 1.0])

    diameter['small']  = fuzz.trimf(diameter.universe, [0.0, 0.0, 0.4])
    diameter['medium'] = fuzz.trimf(diameter.universe, [0.3, 0.55, 0.75])
    diameter['large']  = fuzz.trimf(diameter.universe, [0.6, 1.0, 1.0])

    # Membership for weight (low / mid / high)
    weight['low']  = fuzz.trimf(weight.universe, [0.0, 0.0, 0.4])
    weight['mid']  = fuzz.trimf(weight.universe, [0.3, 0.55, 0.75])
    weight['high'] = fuzz.trimf(weight.universe, [0.6, 1.0, 1.0])

    # Membership for ratio (L/D) - poor/normal/good (higher ratio often desirable)
    ratio['poor']   = fuzz.trimf(ratio.universe, [0.0, 0.0, 0.4])
    ratio['normal'] = fuzz.trimf(ratio.universe, [0.3, 0.55, 0.75])
    ratio['good']   = fuzz.trimf(ratio.universe, [0.6, 1.0, 1.0])

    # Output memberships for score (low/mid/high)
    score['low']  = fuzz.trimf(score.universe, [0, 0, 40])
    score['mid']  = fuzz.trimf(score.universe, [30, 55, 75])
    score['high'] = fuzz.trimf(score.universe, [65, 100, 100])

    # --- Rules ---
    # Principle: weight dominates; size & ratio support/promote higher score.
    rules = [
        # Strong positive: heavy + large -> high score
        ctrl.Rule(weight['high'] & length['large'], score['high']),
        ctrl.Rule(weight['high'] & diameter['large'], score['high']),
        ctrl.Rule(weight['high'] & ratio['good'], score['high']),

        # Medium: mid weight with decent size/ratio -> mid score
        ctrl.Rule(weight['mid'] & (length['medium'] | diameter['medium']), score['mid']),
        ctrl.Rule(weight['mid'] & ratio['normal'], score['mid']),

        # Low weight mostly -> low score (overrides size)
        ctrl.Rule(weight['low'], score['low']),

        # Supportive rules: large size & good ratio increase score even if weight mid
        ctrl.Rule((diameter['large'] & ratio['good']) & weight['mid'], score['high']),

        # If size small and ratio poor -> low score
        ctrl.Rule(length['small'] & ratio['poor'], score['low']),
        ctrl.Rule(diameter['small'] & ratio['poor'], score['low']),
    ]

    return ctrl.ControlSystem(rules)
