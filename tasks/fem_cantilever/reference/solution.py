"""Reference solution (hidden from the agent)."""
import numpy as np
from skfem import (MeshQuad, ElementQuad2, ElementVector, Basis, FacetBasis,
                   BilinearForm, LinearForm, Functional, solve, condense)
from skfem.helpers import ddot, sym_grad, trace


def solve_cantilever(params: dict, nx: int, ny: int) -> float:
    L, h, b, E, nu, P = (params[k] for k in ("L", "h", "b", "E", "nu", "P"))
    mesh = MeshQuad.init_tensor(np.linspace(0, L, nx + 1), np.linspace(-h / 2, h / 2, ny + 1))
    elem = ElementVector(ElementQuad2())
    basis = Basis(mesh, elem)

    mu = E / (2 * (1 + nu))
    lam = E * nu / (1 - nu ** 2)  # plane stress

    @BilinearForm
    def stiffness(u, v, w):
        return b * (2 * mu * ddot(sym_grad(u), sym_grad(v)) + lam * trace(sym_grad(u)) * trace(sym_grad(v)))

    K = stiffness.assemble(basis)

    tip = mesh.facets_satisfying(lambda x: np.isclose(x[0], L))
    fb = FacetBasis(mesh, elem, facets=tip)

    @LinearForm
    def load(v, w):
        y = w.x[1]
        q = -(3 * P / (2 * b * h)) * (1 - 4 * y ** 2 / h ** 2)  # parabolic shear traction
        return b * q * v[1]

    f = load.assemble(fb)
    fixed = basis.get_dofs(lambda x: np.isclose(x[0], 0)).all()
    u = solve(*condense(K, f, D=fixed))

    avg_uy = Functional(lambda w: w["u"][1]).assemble(fb, u=fb.interpolate(u)) / h
    return float(abs(avg_uy))
