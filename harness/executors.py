"""Executors: where the agent's commands run and where solutions get graded.

LocalExecutor  - temp dir on the host. For harness tests / oracle baselines ONLY (no isolation).
DockerExecutor - one container per run, no network. Use this for real agent evaluations.
"""
import json, os, shutil, subprocess, sys, tempfile
from abc import ABC, abstractmethod

TASKS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tasks")
MAX_OUT = 10_000


def task_dir(name): return os.path.abspath(os.path.join(TASKS_DIR, name))
def load_manifest(name):
    with open(os.path.join(task_dir(name), "task.json")) as f: return json.load(f)


def _trunc(s: str) -> str:
    return s if len(s) <= MAX_OUT else s[:MAX_OUT // 2] + "\n...[truncated]...\n" + s[-MAX_OUT // 2:]


def _parse_grade(stdout: str) -> dict:
    try:
        return json.loads(stdout)
    except Exception:
        return dict(passed=False, score=0.0, checks={"grader_output_valid": False},
                    detail={"stdout": stdout[-500:]})


class Executor(ABC):
    def __init__(self, task: str):
        self.task, self.manifest, self.tdir = task, load_manifest(task), task_dir(task)

    def __enter__(self): self.start(); return self
    def __exit__(self, *a): self.stop()

    @abstractmethod
    def start(self): ...
    @abstractmethod
    def stop(self): ...
    @abstractmethod
    def bash(self, cmd: str, timeout: int = 120) -> str: ...
    @abstractmethod
    def write_file(self, path: str, content: str) -> str: ...
    @abstractmethod
    def read_file(self, path: str) -> str: ...
    @abstractmethod
    def grade(self) -> dict: ...

    def task_prompt(self) -> str:
        return open(os.path.join(self.tdir, self.manifest["prompt_file"])).read()

    def starter_solution(self) -> str:
        return open(os.path.join(self.tdir, self.manifest["workspace_files"]["solution.py"])).read()


class LocalExecutor(Executor):
    def preflight(self):
        """Fail fast on a broken environment instead of mis-scoring it as an agent crash."""
        import importlib.util
        missing = [m for m in self.manifest.get("requires", []) if importlib.util.find_spec(m) is None]
        if missing:
            raise EnvironmentError(
                f"missing Python packages {missing} for interpreter {sys.executable}. "
                f"Install with: {sys.executable} -m pip install -r requirements.txt")

    def start(self):
        self.preflight()
        self.ws = tempfile.mkdtemp(prefix=f"engbench_{self.task}_")
        for dest, src in self.manifest["workspace_files"].items():
            shutil.copy(os.path.join(self.tdir, src), os.path.join(self.ws, dest))

    def stop(self): shutil.rmtree(self.ws, ignore_errors=True)

    def _safe(self, path):
        full = os.path.realpath(os.path.join(self.ws, path.lstrip("/").removeprefix("workspace/")))
        if not full.startswith(os.path.realpath(self.ws) + os.sep):
            raise ValueError("path escapes workspace")
        return full

    def bash(self, cmd, timeout=120):
        try:
            p = subprocess.run(["bash", "-c", cmd], cwd=self.ws, capture_output=True, text=True, timeout=timeout)
            return _trunc(f"[exit {p.returncode}]\n{p.stdout}{p.stderr}")
        except subprocess.TimeoutExpired:
            return f"[timeout after {timeout}s]"

    def write_file(self, path, content):
        full = self._safe(path); os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w") as f: f.write(content)
        return f"wrote {len(content)} bytes to {path}"

    def read_file(self, path): return open(self._safe(path)).read()

    def grade(self):
        sol = os.path.join(self.ws, "solution.py")
        try:
            p = subprocess.run([sys.executable, os.path.join(self.tdir, "grader.py"), sol], cwd=self.tdir,
                               capture_output=True, text=True, timeout=self.manifest["grade_timeout_s"])
            return _parse_grade(p.stdout)
        except subprocess.TimeoutExpired:
            return dict(passed=False, score=0.0, checks={"grader_timeout": False}, detail={})


class DockerExecutor(Executor):
    """Untested in the dev sandbox (no Docker there) - run `pytest -m docker` on a machine with Docker."""
    def start(self):
        self.image = f"engbench-{self.task}"
        subprocess.run(["docker", "build", "-q", "-t", self.image, self.tdir], check=True, capture_output=True)
        out = subprocess.run(["docker", "run", "-d", "--rm", "--network", "none", "--memory", "4g", "--cpus", "2",
                              self.image, "sleep", "infinity"], check=True, capture_output=True, text=True)
        self.cid = out.stdout.strip()

    def stop(self): subprocess.run(["docker", "rm", "-f", self.cid], capture_output=True)

    def bash(self, cmd, timeout=120):
        try:
            p = subprocess.run(["docker", "exec", "-w", "/workspace", self.cid, "bash", "-c", cmd],
                               capture_output=True, text=True, timeout=timeout)
            return _trunc(f"[exit {p.returncode}]\n{p.stdout}{p.stderr}")
        except subprocess.TimeoutExpired:
            return f"[timeout after {timeout}s]"

    def write_file(self, path, content):
        if not path.startswith("/"): path = "/workspace/" + path
        subprocess.run(["docker", "exec", "-i", self.cid, "bash", "-c", f"cat > '{path}'"],
                       input=content, text=True, check=True)
        return f"wrote {len(content)} bytes to {path}"

    def read_file(self, path):
        if not path.startswith("/"): path = "/workspace/" + path
        return subprocess.run(["docker", "exec", self.cid, "cat", path], capture_output=True, text=True).stdout

    def grade(self):
        # Grade in a FRESH container: grader + reference are mounted read-only, never visible to the agent.
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(["docker", "cp", f"{self.cid}:/workspace/solution.py", os.path.join(tmp, "solution.py")], check=True)
            try:
                p = subprocess.run(["docker", "run", "--rm", "--network", "none",
                                    "-v", f"{self.tdir}:/grader:ro", "-v", f"{tmp}:/sol:ro", "-w", "/grader",
                                    self.image, "python", "/grader/grader.py", "/sol/solution.py"],
                                   capture_output=True, text=True, timeout=self.manifest["grade_timeout_s"])
                return _parse_grade(p.stdout)
            except subprocess.TimeoutExpired:
                return dict(passed=False, score=0.0, checks={"grader_timeout": False}, detail={})
