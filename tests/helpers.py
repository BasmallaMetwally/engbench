import importlib.util, os, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tasks")


def task_grade(task: str, solution_path: str) -> dict:
    """Load tasks/<task>/grader.py under a unique module name and grade a solution file."""
    tdir = os.path.abspath(os.path.join(ROOT, task))
    if tdir not in sys.path:
        sys.path.insert(0, tdir)
    spec = importlib.util.spec_from_file_location(f"grader_{task}", os.path.join(tdir, "grader.py"))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod.grade(solution_path)


def ref(task): return os.path.join(ROOT, task, "reference", "solution.py")
def starter(task): return os.path.join(ROOT, task, "starter", "solution.py")
