"""Agents. Each takes an Executor + task prompt and tries to produce /workspace/solution.py."""
import os
from abc import ABC, abstractmethod


class Agent(ABC):
    name = "agent"
    model = None

    @abstractmethod
    def run(self, ex, prompt: str, max_steps: int) -> dict:
        """Return dict(steps, input_tokens, output_tokens, transcript, error)."""


class NullAgent(Agent):
    """Does nothing -> measures the 'untouched starter' floor (must score 0)."""
    name = "null"

    def run(self, ex, prompt, max_steps):
        return dict(steps=0, input_tokens=0, output_tokens=0, transcript=[], error=None)


class OracleAgent(Agent):
    """Copies the hidden reference solution -> proves every task is solvable (the ceiling)."""
    name = "oracle"

    def run(self, ex, prompt, max_steps):
        ref = open(os.path.join(ex.tdir, "reference", "solution.py")).read()
        ex.write_file("solution.py", ref)
        return dict(steps=1, input_tokens=0, output_tokens=0, transcript=[], error=None)


class CommandAgent(Agent):
    """Runs ANY external agent as a shell command inside the workspace."""

    def __init__(self, cmd: str, name: str = "cmd", timeout: int = 300):
        self.cmd, self.name, self.timeout = cmd, name, timeout

    def run(self, ex, prompt, max_steps):
        result = ex.bash_capture(self.cmd, timeout=self.timeout)
        err = "timeout" if result["timed_out"] else None
        return dict(steps=1, input_tokens=0, output_tokens=0,
                    transcript=[{"role": "agent", **result}], error=err)
