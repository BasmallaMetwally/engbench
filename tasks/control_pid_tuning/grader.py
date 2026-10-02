"""Deterministic grader: simulates the closed loop for the agent's PID on HIDDEN plants."""
import importlib.util, json, math, sys, time
from sim import make_plant, simulate, metrics

HIDDEN_SEEDS = [101, 202, 303]
ROBUST_OS_MAX = 20.0      # % overshoot under +-20% gain / +20% delay error
SSE_MAX = 0.01
DIST = 0.2


def load(path):
    spec = importlib.util.spec_from_file_location("agent_solution", path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m.design_pid


def grade(path: str) -> dict:
    t0, checks, detail = time.time(), {}, {}
    try:
        design = load(path)
        names = ["nominal_stable", "overshoot", "settling_time", "steady_state_error",
                 "robust_gain_delay", "disturbance_rejection"]
        ok = {n: True for n in names}
        for s in HIDDEN_SEEDS:
            p = make_plant(s)
            g = design(dict(p))
            g = {k: float(g[k]) for k in ("Kp", "Ki", "Kd")}
            assert all(math.isfinite(v) and v >= 0 for v in g.values()), f"bad gains {g}"
            T = 3 * p["ts_max"]
            m = metrics(*simulate(p, g, T)[:2])
            ok["nominal_stable"] &= m["stable"]
            ok["overshoot"] &= m["overshoot"] <= p["os_max"]
            ok["settling_time"] &= m["settling"] <= p["ts_max"]
            ok["steady_state_error"] &= m["sse"] <= SSE_MAX
            rob = [metrics(*simulate(p, g, T, gain_scale=gs, delay_scale=ds)[:2])
                   for gs, ds in ((1.2, 1.2), (0.8, 1.0))]
            ok["robust_gain_delay"] &= all(r["stable"] and r["overshoot"] <= ROBUST_OS_MAX
                                           and r["sse"] <= SSE_MAX for r in rob)
            d = metrics(*simulate(p, g, T, dist=DIST, t_dist=T / 2)[:2])
            ok["disturbance_rejection"] &= d["stable"] and d["sse"] <= SSE_MAX
            detail[f"seed{s}"] = dict(gains=g, overshoot=round(m["overshoot"], 2),
                                      settling=round(m["settling"], 2), ts_max=round(p["ts_max"], 2))
        checks = {k: bool(v) for k, v in ok.items()}
    except Exception as e:
        checks = {"runs_without_error": False}; detail = {"error": repr(e)}
    return dict(passed=bool(all(checks.values())), score=sum(checks.values()) / len(checks),
                checks=checks, detail=detail, seconds=round(time.time() - t0, 2))


if __name__ == "__main__":
    res = grade(sys.argv[1] if len(sys.argv) > 1 else "/workspace/solution.py")
    print(json.dumps(res, indent=2)); sys.exit(0 if res["passed"] else 1)
