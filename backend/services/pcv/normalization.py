# services/pcv/normalization.py
import numpy as np

def normalize_pct(value, series, low_pct=5, high_pct=95):
    lo = np.percentile(series, low_pct)
    hi = np.percentile(series, high_pct)
    return float(np.clip((value - lo) / (hi - lo + 1e-9), 0, 1))

def normalize_fixed(value, lo, hi):
    return float(np.clip((value - lo) / (hi - lo + 1e-9), 0, 1))
