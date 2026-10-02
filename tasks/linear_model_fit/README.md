# Task: Fit a line from noisy samples

Implement `fit_line(samples)` in `/workspace/solution.py`.

The input is a list of samples, each sample is either:
- a dict with keys `x` and `y`, or
- a 2-tuple `(x, y)`.

The target is a line `y = a * x + b` with small noise. Return the coefficients as a 2-tuple `(a, b)`.

## Requirements

The grader evaluates the function on hidden seeds and checks that:
1. the fitted slope is close to the true slope,
2. the fitted intercept is close to the true intercept,
3. the prediction error on hidden points is low,
4. the implementation does not crash and returns finite values.

Use the exact hidden data generator from the grader if needed; do not modify the grader.

Your solution should be robust to a few outliers and avoid using any external packages beyond NumPy.
