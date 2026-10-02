"""Seeded instance generator + analytical reference (shared by grader and CI)."""
import json, sys
import numpy as np


def make_params(seed: int) -> dict:
    rng = np.random.default_rng(seed)
    L = float(rng.uniform(0.8, 1.5))            # m
    h = float(L / rng.uniform(8, 12))           # m  (slender beam)
    b = float(rng.uniform(0.02, 0.06))          # m  (thickness)
    E = float(rng.uniform(60e9, 210e9))         # Pa
    nu = float(rng.uniform(0.25, 0.35))
    P = float(rng.uniform(500, 3000))           # N, downward tip load
    return dict(L=L, h=h, b=b, E=E, nu=nu, P=P)


def analytical_deflection(p: dict) -> float:
    """Euler-Bernoulli + Timoshenko shear term (kappa = 5/6). Magnitude, metres."""
    I = p["b"] * p["h"] ** 3 / 12
    A = p["b"] * p["h"]
    G = p["E"] / (2 * (1 + p["nu"]))
    return p["P"] * p["L"] ** 3 / (3 * p["E"] * I) + p["P"] * p["L"] / ((5 / 6) * G * A)


if __name__ == "__main__":
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    json.dump(make_params(seed), sys.stdout, indent=2)
