"""Deterministic grader. Imports the agent's solution.py and tests it on HIDDEN instances."""
import importlib.util, json, sys, time
import numpy as np
from instance import make_params, analytical_deflection

TOL = 0.05            # 5% vs analytical (includes clamped-end effect)
CONV_TOL = 0.02       # last refinement must change result < 2%
HIDDEN_SEEDS = [101, 202, 303]   # not shown to the agent
MESHES = [(8, 2), (16, 4), (32, 8)]
STUBBY = dict(L=0.4, h=0.2, b=0.05, E=70e9, nu=0.33, P=20000.0)  # L/h=2: beam theory fails here
STUBBY_TOL = 0.03


def load_ref():
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    return load(os.path.join(here, "reference", "solution.py"))


def load(path):
    spec = importlib.util.spec_from_file_location("agent_solution", path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m.solve_cantilever


def grade(path: str) -> dict:
    checks, t0 = {}, time.time()
    try:
        fn = load(path)
        errs, convs, scale = [], [], []
        for s in HIDDEN_SEEDS:
            p = make_params(s); ref = analytical_deflection(p)
            vals = [fn(p, nx, ny) for nx, ny in MESHES]
            errs.append(abs(vals[-1] - ref) / ref)
            convs.append(abs(vals[-1] - vals[-2]) / vals[-1])
            # linearity: doubling load must double deflection
            p2 = dict(p, P=2 * p["P"])
            scale.append(abs(fn(p2, *MESHES[-1]) / vals[-1] - 2.0))
        # must be a real discretisation: result has to react to the mesh
        coarse = fn(make_params(HIDDEN_SEEDS[0]), 2, 1)
        fine = fn(make_params(HIDDEN_SEEDS[0]), *MESHES[-1])
        checks["depends_on_mesh"] = bool(abs(coarse - fine) / fine > 1e-4)
        # thick beam: closed-form beam theory is wrong here, FEM is not
        truth = load_ref()(STUBBY, 64, 32)
        checks["stubby_matches_fem"] = bool(abs(fn(STUBBY, 32, 16) - truth) / truth < STUBBY_TOL)
        checks["accuracy_vs_analytical"] = bool(max(errs) < TOL)
        checks["mesh_convergence"] = bool(max(convs) < CONV_TOL)
        checks["linear_in_load"] = bool(max(scale) < 1e-6)
        detail = dict(max_rel_error=float(max(errs)), max_conv_change=float(max(convs)))
    except Exception as e:  # any crash = fail
        checks = {"runs_without_error": False}; detail = {"error": repr(e)}
    score = sum(checks.values()) / max(len(checks), 1)
    return dict(passed=bool(all(checks.values())), score=score, checks=checks,
                detail=detail, seconds=round(time.time() - t0, 2))


if __name__ == "__main__":
    res = grade(sys.argv[1] if len(sys.argv) > 1 else "/workspace/solution.py")
    print(json.dumps(res, indent=2)); sys.exit(0 if res["passed"] else 1)
