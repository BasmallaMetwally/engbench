# Task: Cantilever beam tip deflection (FEM)

Implement `solve_cantilever(params, nx, ny)` in `/workspace/solution.py`.

It must solve a **2D plane-stress** linear-elastic cantilever with the finite-element method
and return the **magnitude of the tip deflection** (metres), averaged over the free end.

## Setup
- Domain: rectangle `x in [0, L]`, `y in [-h/2, h/2]`, thickness `b`.
- Material: Young's modulus `E`, Poisson ratio `nu`, plane stress.
- Left end (`x = 0`): fully clamped (u = 0).
- Right end (`x = L`): total downward force `P`, applied as a **parabolic shear traction**
  `q(y) = -3P / (2 b h) * (1 - 4y^2/h^2)` (per unit area, acting in -y).
- Mesh: structured, `nx` elements along `x`, `ny` along `y`.
- All inputs in SI units. See `example_params.json`.

## Rules
- Use FEM (`scikit-fem`, NumPy, SciPy are installed). Closed-form beam formulas alone will fail.
- Your function is tested on **hidden** parameter sets and several mesh sizes,
  so do not hard-code values.
- Don't read or modify anything outside `/workspace`.

## You are graded on
1. Agreement with beam theory (incl. shear) within 5% on slender beams
2. Mesh convergence
3. Linearity in the load `P`
4. Result genuinely depends on the mesh (a real discretisation)
5. Agreement (3%) with a high-fidelity FEM reference on a thick beam (L/h = 2)
