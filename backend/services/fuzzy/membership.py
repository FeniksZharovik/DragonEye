# file: services/fuzzy/membership.py
import numpy as np

def get_memberships():
    """
    Return universes (numpy arrays) for fuzzy variables.
    - length: normalized 0..1 (cm mapped externally)
    - diameter: normalized 0..1 (cm mapped externally)
    - weight: normalized 0..1 (g mapped externally)
    - ratio: normalized 0..1 (L/D mapped externally)
    - score: output universe 0..100
    """
    length = np.linspace(0, 1, 101)
    diameter = np.linspace(0, 1, 101)
    weight = np.linspace(0, 1, 101)
    ratio = np.linspace(0, 1, 101)
    score = np.linspace(0, 100, 101)

    return length, diameter, weight, ratio, score
