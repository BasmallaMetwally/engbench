import importlib.util
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MUTATION_SCORE_THRESHOLD = 0.90


def _load_grader(task: str):
    path = ROOT / "tasks" / task / "grader.py"
    task_dir = str(path.parent)
    if task_dir not in sys.path:
        sys.path.insert(0, task_dir)
    spec = importlib.util.spec_from_file_location(f"grader_{task}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.grade


def _write_mutant(task: str, mutant_name: str, body: str, tmp_path: Path) -> str:
    target = tmp_path / f"{task}_{mutant_name}.py"
    target.write_text(body)
    return str(target)


def _wrap_reference(ref_src: str, func_name: str, override: str) -> str:
    renamed = ref_src.strip().replace(f"def {func_name}", f"def _orig_{func_name}", 1)
    return textwrap.dedent(f"""
        {renamed}

        def {func_name}(*args, **kwargs):
            {override}
    """)


def _fem_mutants(ref_src: str):
    mutants = {}
    mutants["flip_sign"] = _wrap_reference(ref_src, "solve_cantilever", "return -_orig_solve_cantilever(*args, **kwargs)")
    mutants["scale_up"] = _wrap_reference(ref_src, "solve_cantilever", "return 1.2 * _orig_solve_cantilever(*args, **kwargs)")
    mutants["scale_down"] = _wrap_reference(ref_src, "solve_cantilever", "return 0.6 * _orig_solve_cantilever(*args, **kwargs)")
    mutants["zero_out"] = _wrap_reference(ref_src, "solve_cantilever", "return 0.0")
    mutants["coarse_override"] = _wrap_reference(
        ref_src,
        "solve_cantilever",
        "params, nx, ny = args[0], args[1], args[2]; return _orig_solve_cantilever({**params, 'P': params['P'] * 0.1}, max(2, nx // 2), max(1, ny // 2))",
    )
    return mutants


def _pid_mutants(ref_src: str):
    mutants = {}
    mutants["ki_zero"] = _wrap_reference(ref_src, "design_pid", "g = _orig_design_pid(*args, **kwargs); g['Ki'] = 0.0; return g")
    mutants["kd_zero"] = _wrap_reference(ref_src, "design_pid", "g = _orig_design_pid(*args, **kwargs); g['Kd'] = 0.0; return g")
    mutants["kp_times_3"] = _wrap_reference(ref_src, "design_pid", "g = _orig_design_pid(*args, **kwargs); g['Kp'] *= 3.0; g['Ki'] *= 3.0; return g")
    mutants["gain_scale_down"] = _wrap_reference(ref_src, "design_pid", "g = _orig_design_pid(*args, **kwargs); g['Kp'] *= 0.3; g['Ki'] *= 0.3; g['Kd'] *= 0.3; return g")
    mutants["constant_bad_gains"] = textwrap.dedent("""
        import os, sys
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
        from sim import simulate, metrics

        def design_pid(plant: dict) -> dict:
            return {"Kp": 100.0, "Ki": 0.0, "Kd": 0.0}
    """)
    return mutants


def _linear_mutants(ref_src: str):
    mutants = {}
    mutants["modulus_halved"] = _wrap_reference(ref_src, "fit_line", "modulus, offset = _orig_fit_line(*args, **kwargs); return 0.5 * modulus, offset")
    mutants["modulus_doubled"] = _wrap_reference(ref_src, "fit_line", "modulus, offset = _orig_fit_line(*args, **kwargs); return 2.0 * modulus, offset")
    mutants["offset_shifted"] = _wrap_reference(ref_src, "fit_line", "modulus, offset = _orig_fit_line(*args, **kwargs); return modulus, offset + 25.0")
    mutants["bad_constant"] = textwrap.dedent("""
        def fit_line(samples):
            return 0.0, 0.0
    """)
    return mutants


def _mutant_results(task: str, tmp_path: Path, mutants):
    grade = _load_grader(task)
    results = []
    for name, body in mutants.items():
        path = _write_mutant(task, name, body, tmp_path)
        score = grade(path)
        results.append((name, score))
    return results


def test_mutant_suite_rejects_broken_reference_variants(tmp_path):
    cases = {
        "fem_cantilever": _fem_mutants((ROOT / "tasks" / "fem_cantilever" / "reference" / "solution.py").read_text()),
        "control_pid_tuning": _pid_mutants((ROOT / "tasks" / "control_pid_tuning" / "reference" / "solution.py").read_text()),
        "linear_model_fit": _linear_mutants((ROOT / "tasks" / "linear_model_fit" / "reference" / "solution.py").read_text()),
    }

    total = 0
    killed = 0
    mutation_rows = []
    for task, mutants in cases.items():
        for name, grade in _mutant_results(task, tmp_path, mutants):
            total += 1
            mutation_rows.append({"task": task, "mutant": name, "killed": int(not grade["passed"]), "passed": bool(grade["passed"])})
            if not grade["passed"]:
                killed += 1
            else:
                raise AssertionError(f"mutation '{task}:{name}' survived: grade={grade!r}")

    score = killed / total
    assert score >= MUTATION_SCORE_THRESHOLD, f"mutation score too low: {score:.2%} ({killed}/{total})"
    print(f"mutation score: {score:.2%} ({killed}/{total})")
    assert score >= MUTATION_SCORE_THRESHOLD
