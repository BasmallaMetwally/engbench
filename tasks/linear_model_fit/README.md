# Task: Characterize a material from tensile-test data

Implement `fit_line(samples)` in `/workspace/solution.py`.

The samples come from a uniaxial tensile test in the material's linear-elastic range. Each sample is either a dict with `x` and `y` keys or a 2-tuple `(strain, stress_mpa)`. Here `x` is dimensionless engineering strain and `y` is measured stress in MPa.

Assume the measurement model `stress = E * strain + offset`, where `E` is Young's modulus in MPa and `offset` is a small stress-zero measurement bias in MPa. Return `(E, offset)` as a 2-tuple.

## Requirements

The grader evaluates hidden, seeded tensile-test datasets and checks that the estimated modulus and stress offset are close to their generating values, predictions have low mean-squared error, and all returned values are finite.

The task is complete when the reference passes, the starter fails, and at least four deliberately incorrect material models fail. Use NumPy; do not modify the grader or rely on hidden data.
