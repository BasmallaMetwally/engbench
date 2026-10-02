import importlib.util, json, math, sys, time

HIDDEN_SEEDS = [7, 13, 29]


def make_samples(seed: int):
    import numpy as np
    rng = np.random.default_rng(seed)
    modulus_mpa = float(rng.uniform(60_000.0, 210_000.0))
    stress_offset_mpa = float(rng.uniform(-5.0, 5.0))
    strains = np.linspace(0.0001, 0.0025, 25)
    stresses = modulus_mpa * strains + stress_offset_mpa + rng.normal(0.0, 1.0, size=strains.shape)
    samples = [{"x": float(strain), "y": float(stress)} for strain, stress in zip(strains, stresses)]
    return dict(modulus_mpa=modulus_mpa, stress_offset_mpa=stress_offset_mpa, samples=samples)


def load(path):
    spec = importlib.util.spec_from_file_location("agent_solution", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.fit_line


def normalize(pred, samples):
    if isinstance(pred, dict):
        return float(pred["youngs_modulus_mpa"]), float(pred["stress_offset_mpa"])
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
            modulus_hat, offset_hat = normalize(pred, data["samples"])
            modulus_err = abs(modulus_hat - data["modulus_mpa"])
            offset_err = abs(offset_hat - data["stress_offset_mpa"])
            xs = [item["x"] for item in data["samples"]]
            ys = [item["y"] for item in data["samples"]]
            y_pred = [modulus_hat * strain + offset_hat for strain in xs]
            mse = sum((yp - y) ** 2 for yp, y in zip(y_pred, ys)) / len(ys)
            ok &= math.isfinite(modulus_hat) and math.isfinite(offset_hat)
            ok &= modulus_err <= 800.0
            ok &= offset_err <= 2.5
            ok &= mse <= 2.5
            detail[f"seed{s}"] = {
                "youngs_modulus_mpa": round(modulus_hat, 2),
                "stress_offset_mpa": round(offset_hat, 4),
                "modulus_error_mpa": round(modulus_err, 2),
                "offset_error_mpa": round(offset_err, 4),
                "mse_mpa2": round(mse, 4),
            }
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
