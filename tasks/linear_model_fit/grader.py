import importlib.util, json, math, sys, time

HIDDEN_SEEDS = [7, 13, 29]


def make_samples(seed: int):
    import numpy as np
    rng = np.random.default_rng(seed)
    modulus_mpa = float(rng.uniform(90_000.0, 210_000.0))
    stress_offset_mpa = float(rng.uniform(-15.0, 15.0))
    yield_strain = float(rng.uniform(0.0025, 0.0050))
    hardening_mpa = modulus_mpa * float(rng.uniform(0.04, 0.12))
    strains = np.linspace(0.0, 0.02, 81)
    elastic_strain = np.minimum(strains, yield_strain)
    plastic_strain = np.maximum(strains - yield_strain, 0.0)
    stresses = (
        stress_offset_mpa
        + modulus_mpa * elastic_strain
        + hardening_mpa * plastic_strain
        + rng.normal(0.0, 2.0, size=strains.shape)
    )
    elastic_indices = np.flatnonzero(strains < yield_strain)
    plastic_indices = np.flatnonzero(strains > yield_strain)
    outlier_indices = [int(rng.choice(elastic_indices))]
    outlier_indices.extend(int(i) for i in rng.choice(plastic_indices, size=2, replace=False))
    stresses[outlier_indices] += rng.choice([-1.0, 1.0], size=3) * rng.uniform(70.0, 140.0, size=3)
    samples = [{"x": float(strain), "y": float(stress)} for strain, stress in zip(strains, stresses)]
    return dict(
        modulus_mpa=modulus_mpa,
        stress_offset_mpa=stress_offset_mpa,
        yield_strain=yield_strain,
        samples=samples,
    )


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
        seed_checks = {"modulus_accuracy": [], "offset_accuracy": [], "elastic_fit_error": []}
        for s in HIDDEN_SEEDS:
            data = make_samples(s)
            pred = fn(data["samples"])
            modulus_hat, offset_hat = normalize(pred, data["samples"])
            modulus_err = abs(modulus_hat - data["modulus_mpa"])
            offset_err = abs(offset_hat - data["stress_offset_mpa"])
            elastic = [item for item in data["samples"] if item["x"] < data["yield_strain"]]
            residuals = [modulus_hat * item["x"] + offset_hat - item["y"] for item in elastic]
            elastic_mse = sum(residual * residual for residual in residuals) / len(residuals)
            finite = math.isfinite(modulus_hat) and math.isfinite(offset_hat)
            seed_checks["modulus_accuracy"].append(finite and modulus_err <= 0.04 * data["modulus_mpa"])
            seed_checks["offset_accuracy"].append(finite and offset_err <= 5.0)
            seed_checks["elastic_fit_error"].append(finite and elastic_mse <= 1200.0)
            detail[f"seed{s}"] = {
                "youngs_modulus_mpa": round(modulus_hat, 2),
                "stress_offset_mpa": round(offset_hat, 4),
                "modulus_error_mpa": round(modulus_err, 2),
                "offset_error_mpa": round(offset_err, 4),
                "elastic_mse_mpa2": round(elastic_mse, 4),
            }
        checks = {name: all(values) for name, values in seed_checks.items()}
    except Exception as e:
        checks = {"runs_without_error": False}
        detail = {"error": repr(e)}
    score = sum(checks.values()) / max(len(checks), 1)
    return dict(passed=bool(all(checks.values())), score=score, checks=checks, detail=detail, seconds=round(time.time() - t0, 2))


if __name__ == "__main__":
    res = grade(sys.argv[1] if len(sys.argv) > 1 else "/workspace/solution.py")
    print(json.dumps(res, indent=2))
    sys.exit(0 if res["passed"] else 1)
