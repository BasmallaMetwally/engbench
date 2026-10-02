"""Implement `design_pid` (see README.md)."""
import numpy as np
from scipy import optimize
from sim import simulate, metrics   # same simulator the grader uses


def design_pid(plant: dict) -> dict:
    """plant: K, tau1, tau2, theta, umax, os_max (%), ts_max (s).
    Return {"Kp": ..., "Ki": ..., "Kd": ...} (all >= 0)."""
    # TODO
    raise NotImplementedError
