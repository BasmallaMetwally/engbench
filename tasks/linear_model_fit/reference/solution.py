import numpy as np


def _robust_line(xs, ys):
    left, right = np.triu_indices(xs.size, 1)
    slopes = (ys[right] - ys[left]) / (xs[right] - xs[left])
    slope = float(np.median(slopes))
    intercept = float(np.median(ys - slope * xs))
    return slope, intercept


def fit_line(samples):
    xs = np.asarray([item["x"] if isinstance(item, dict) else item[0] for item in samples], dtype=float)
    ys = np.asarray([item["y"] if isinstance(item, dict) else item[1] for item in samples], dtype=float)
    order = np.argsort(xs)
    xs, ys = xs[order], ys[order]
    min_segment = max(8, xs.size // 10)
    best_score, best_line = float("inf"), None

    for split in range(min_segment, xs.size - min_segment + 1):
        elastic_slope, elastic_intercept = _robust_line(xs[:split], ys[:split])
        post_slope, post_intercept = _robust_line(xs[split:], ys[split:])
        residuals = np.concatenate((
            np.abs(ys[:split] - (elastic_slope * xs[:split] + elastic_intercept)),
            np.abs(ys[split:] - (post_slope * xs[split:] + post_intercept)),
        ))
        score = float(np.square(np.minimum(residuals, 12.0)).sum())
        if score < best_score:
            best_score = score
            best_line = elastic_slope, elastic_intercept

    if best_line is None:
        raise ValueError("not enough samples to identify elastic and post-yield regions")
    return best_line
