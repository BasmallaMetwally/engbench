import importlib.util
import textwrap
from pathlib import Path

from helpers import ref, starter, task_grade


TASK = "linear_model_fit"


def _write_solution(tmp_path, name, body):
    path = tmp_path / f"{name}.py"
    path.write_text(body)
    return str(path)


def test_reference_passes():
    assert task_grade(TASK, ref(TASK))["passed"]


def test_starter_fails():
    assert not task_grade(TASK, starter(TASK))["passed"]


def test_four_incorrect_material_models_fail(tmp_path):
    reference_source = open(ref(TASK), encoding="utf-8").read()
    renamed_reference = reference_source.replace("def fit_line", "def _reference_fit_line", 1)
    overrides = {
        "modulus_halved": "modulus, offset = _reference_fit_line(*args, **kwargs); return 0.5 * modulus, offset",
        "modulus_doubled": "modulus, offset = _reference_fit_line(*args, **kwargs); return 2.0 * modulus, offset",
        "offset_shifted": "modulus, offset = _reference_fit_line(*args, **kwargs); return modulus, offset + 25.0",
        "constant_model": "return 0.0, 0.0",
    }

    for name, override in overrides.items():
        body = textwrap.dedent(f"""
            {renamed_reference}

            def fit_line(*args, **kwargs):
                {override}
        """)
        assert not task_grade(TASK, _write_solution(tmp_path, name, body))["passed"], name


def test_global_polyfit_fails_to_identify_elastic_modulus(tmp_path):
    body = textwrap.dedent("""
        import numpy as np

        def fit_line(samples):
            xs = np.asarray([item["x"] if isinstance(item, dict) else item[0] for item in samples])
            ys = np.asarray([item["y"] if isinstance(item, dict) else item[1] for item in samples])
            slope, offset = np.polyfit(xs, ys, 1)
            return float(slope), float(offset)
    """)
    result = task_grade(TASK, _write_solution(tmp_path, "global_polyfit", body))
    assert not result["checks"]["modulus_accuracy"]


def test_systematic_modulus_bias_exceeds_calibrated_tolerance(tmp_path):
    reference_source = open(ref(TASK), encoding="utf-8").read()
    renamed_reference = reference_source.replace("def fit_line", "def _reference_fit_line", 1)
    body = (
        f"{renamed_reference}\n\n"
        "def fit_line(*args, **kwargs):\n"
        "    modulus, offset = _reference_fit_line(*args, **kwargs)\n"
        "    return 1.03 * modulus, offset\n"
    )
    result = task_grade(TASK, _write_solution(tmp_path, "modulus_bias_3pct", body))
    assert not result["checks"]["modulus_accuracy"]


def test_systematic_offset_bias_exceeds_calibrated_tolerance(tmp_path):
    reference_source = open(ref(TASK), encoding="utf-8").read()
    renamed_reference = reference_source.replace("def fit_line", "def _reference_fit_line", 1)
    body = (
        f"{renamed_reference}\n\n"
        "def fit_line(*args, **kwargs):\n"
        "    modulus, offset = _reference_fit_line(*args, **kwargs)\n"
        "    return modulus, offset + 6.0\n"
    )
    result = task_grade(TASK, _write_solution(tmp_path, "offset_bias_6mpa", body))
    assert not result["checks"]["offset_accuracy"]


def test_reference_generalizes_to_unseen_noisy_outlier_curves():
    grader_path = Path(__file__).resolve().parents[1] / "tasks" / TASK / "grader.py"
    spec = importlib.util.spec_from_file_location("linear_model_fit_stress_test_grader", grader_path)
    grader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(grader)
    fit_line = grader.load(ref(TASK))

    for seed in range(100, 120):
        data = grader.make_samples(seed, noise_std=6.0, outlier_range=(250.0, 400.0))
        modulus_hat, offset_hat = fit_line(data["samples"])
        assert abs(modulus_hat - data["modulus_mpa"]) <= 0.07 * data["modulus_mpa"], seed
        assert abs(offset_hat - data["stress_offset_mpa"]) <= 12.0, seed