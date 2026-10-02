"""
Implement `solve_cantilever` (see README.md).
"""
import numpy as np
from skfem import *  # scikit-fem is installed


def solve_cantilever(params: dict, nx: int, ny: int) -> float:
    """Return |tip deflection| in metres for a plane-stress cantilever.

    params: L, h, b, E, nu, P   (SI units)
    nx, ny: number of elements along length / height
    """
    # TODO: mesh -> element -> stiffness (plane stress) -> BCs -> load -> solve
    raise NotImplementedError
