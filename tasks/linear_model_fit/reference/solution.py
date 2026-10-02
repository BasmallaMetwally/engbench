import numpy as np


def fit_line(samples):
    xs = np.asarray([item["x"] if isinstance(item, dict) else item[0] for item in samples], dtype=float)
    ys = np.asarray([item["y"] if isinstance(item, dict) else item[1] for item in samples], dtype=float)
    A = np.column_stack([xs, np.ones_like(xs)])
    coeffs, *_ = np.linalg.lstsq(A, ys, rcond=None)
    return float(coeffs[0]), float(coeffs[1])
