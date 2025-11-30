# file: services/fuzzy/mamdani.py
from skfuzzy import control as ctrl

_controller = None

def get_fuzzy_sim():
    """
    Returns a ControlSystemSimulation instance.
    Builds the ControlSystem lazily on first call from rules.build_fuzzy_controller().
    """
    global _controller
    if _controller is None:
        from .rules import build_fuzzy_controller
        cs = build_fuzzy_controller()
        _controller = ctrl.ControlSystem(cs.rules)
    return ctrl.ControlSystemSimulation(_controller)

def compute_fuzzy_score(length_n, diameter_n, weight_n, ratio_n):
    """
    length_n, diameter_n, weight_n, ratio_n are expected normalized values in [0,1].
    Returns fuzzy score in [0,100] (float).
    """
    sim = get_fuzzy_sim()
    sim.input['length'] = float(length_n)
    sim.input['diameter'] = float(diameter_n)
    sim.input['weight'] = float(weight_n)
    sim.input['ratio'] = float(ratio_n)

    try:
        sim.compute()
        score = float(sim.output['score'])
    except Exception:
        score = 0.0
    return score

def grade_from_weight(weight_g):
    """
    Deterministic final grade by weight thresholds:
    - A: > 350 g
    - B: 250 - 350 g (inclusive lower bound)
    - C: < 250 g
    Returns 'A'/'B'/'C'.
    """
    try:
        w = float(weight_g)
    except Exception:
        return None

    if w > 350.0:
        return 'A'
    if 250.0 <= w <= 350.0:
        return 'B'
    return 'C'
