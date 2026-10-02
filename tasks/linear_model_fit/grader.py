import importlib.util, json, math, sys, time

HIDDEN_SEEDS = [7, 13, 29]


def make_samples(seed: int):
    import numpy as np
    rng = np.random.default_rng(seed)
    a = float(rng.uniform(-3.0, 3.0))
    b = float(rng.uniform(-5.0, 5.0))
    xs = np.linspace(-4.0, 4.0, 25)
    ys = a * xs + b + rng.normal(0.0, 0.12, size=xs.shape)
    return dict(a=a, b=b, samples=[{"x": float(x), "y": float(y)} for x, y in zip(xs, ys)])


def load(path):
    spec = importlib.util.spec_from_file_location("agent_solution", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.fit_line


def normalize(pred, samples):
    if isinstance(pred, dict):
        return float(pred["a"]), float(pred["b"])
    if isinstance(pred, (tuple, list)) and len(pred) == 2:
        return float(pred[0]), float(pred[1])
    raise TypeError(f"function must return (a, b) or {'a': ..., 'b': ...}, got {type(pred)!r}")


def grade(path: str) -> dict:
    t0, checks, detail = time.time(), {}, {}
    try:
        fn = load(path)
        ok = True
        for s in HIDDEN_SEEDS:
            data = make_samples(s)
            pred = fn(data["samples"])
            a_hat, b_hat = normalize(pred, data["samples"])
            a_err = abs(a_hat - data["a"])
            b_err = abs(b_hat - data["b"])
            xs = [item["x"] for item in data["samples"]]
            ys = [item["y"] for item in data["samples"]]
            y_pred = [a_hat * x + b_hat for x in xs]
            mse = sum((yp - y) ** 2 for yp, y in zip(y_pred, ys)) / len(ys)
            ok &= math.isfinite(a_hat) and math.isfinite(b_hat)
            ok &= a_err <= 0.35
            ok &= b_err <= 0.6
            ok &= mse <= 0.25
            detail[f"seed{s}"] = {"a": round(a_hat, 4), "b": round(b_hat, 4), "a_err": round(a_err, 4), "b_err": round(b_err, 4), "mse": round(mse, 4)}
        checks = {"fit_close": bool(ok)}
    except Exception as e:
        checks = {"runs_without_error": False}
        detail = {"error": repr(e)}
    score = sum(checks.values()) / max(len(checks), 1)
    return dict(passed=bool(all(checks.values())), score=score, checks=checks, detail=detail, seconds=round(time.time() - t0, 2))


if __name__ == "__main__":
    res = grade(sys.argv[1] if len(sys.argv) > 1 else "/workspace/solution.py")
    print(json.dumps(res, indent=2))
    sys.exit(0 if res["passed"] else 1)
