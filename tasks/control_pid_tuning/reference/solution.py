"""Reference: SIMC initial guess, then Nelder-Mead on the closed-loop simulation (SciPy)."""
import sys, os
import numpy as np
from scipy.optimize import minimize
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from sim import simulate, metrics


def _gains(x):
    Kp, Ti, Td = np.exp(x)
    return dict(Kp=Kp, Ki=Kp / Ti, Kd=Kp * Td)


def design_pid(plant: dict) -> dict:
    K, t1, t2, th = plant["K"], plant["tau1"], plant["tau2"], plant["theta"]
    Kp0 = t1 / (K * 3 * th)
    x0 = np.log([Kp0, min(t1, 8 * th), t2])
    T = 2.0 * plant["ts_max"]

    def cost(x):
        g = _gains(x)
        m = metrics(*simulate(plant, g, T)[:2])
        r = metrics(*simulate(plant, g, T, gain_scale=1.2, delay_scale=1.2)[:2])
        if not (m["stable"] and r["stable"]):
            return 1e6
        return (m["settling"] + 100 * max(0, m["overshoot"] - 6) + 100 * max(0, r["overshoot"] - 14)
                + 100 * m["sse"] + 100 * max(0, r["settling"] - plant["ts_max"]))

    res = minimize(cost, x0, method="Nelder-Mead", options=dict(maxiter=60, xatol=1e-2, fatol=1e-2))
    return _gains(res.x)
