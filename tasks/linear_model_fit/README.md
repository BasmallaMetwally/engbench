# Task: Identify Young's modulus from a tensile curve

Implement `fit_line(samples)` in `/workspace/solution.py`.

The input is a complete uniaxial tensile-test stress-strain curve, including the initial elastic range, yielding, and post-yield strain hardening. It contains measurement noise and a few outliers. Each sample is either a dict with `x` and `y` keys or a 2-tuple `(strain, stress_mpa)`. Here `x` is dimensionless engineering strain and `y` is measured stress in MPa.

Estimate Young's modulus from the elastic portion only; fitting one line to the entire curve is incorrect because the post-yield slope is different. Return `(E, offset)` as a 2-tuple, where `E` is Young's modulus in MPa and `offset` is the stress-zero measurement bias in MPa.

## Requirements

The grader uses hidden seeded curves and checks modulus accuracy, stress-offset accuracy, and residual error over the hidden elastic range. The reference identifies a robust two-segment fit; solutions must identify the elastic-to-yield transition and handle outliers.

Return either `(modulus_mpa, offset_mpa)` or a mapping with `youngs_modulus_mpa` and `stress_offset_mpa`. Use NumPy; do not modify the grader or rely on hidden data.
