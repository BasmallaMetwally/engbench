import json
import os
import time

import numpy as np
import pytest

from analysis.report import check_table, ci, failure_table, load, summarize
from harness.agents import CommandAgent
from harness.executors import LocalExecutor
from harness.run import classify, main, run_one


def _cmd_run(tmp_path, cmd):
    return run_one("fem_cantilever", CommandAgent(cmd), LocalExecutor, 0, 1, str(tmp_path))


def test_command_agent_solves(tmp_path):
    ref = os.path.abspath("tasks/fem_cantilever/reference/solution.py")
    assert _cmd_run(tmp_path, f'cp "{ref}" solution.py')["failure_type"] == "pass"


def test_command_agent_wrong_physics(tmp_path):
    cmd = "printf 'def solve_cantilever(p,nx,ny):\\n    return 0.0123\\n' > solution.py"
    assert _cmd_run(tmp_path, cmd)["failure_type"] == "wrong_physics"


def test_command_agent_crash(tmp_path):
    cmd = "printf 'def solve_cantilever(p,nx,ny):\\n    raise RuntimeError\\n' > solution.py"
    assert _cmd_run(tmp_path, cmd)["failure_type"] == "crash"


def test_command_agent_stdout_stderr_are_saved(tmp_path):
    rec = _cmd_run(tmp_path, "printf 'agent stdout'; printf 'agent stderr' >&2")
    transcript_path = tmp_path / "transcripts" / "fem_cantilever__cmd__0.json"
    transcript = json.loads(transcript_path.read_text())
    assert rec["failure_type"] != "agent_timeout"
    assert transcript[0]["stdout"] == "agent stdout"
    assert transcript[0]["stderr"] == "agent stderr"
    assert transcript[0]["return_code"] == 0


def test_command_agent_timeout(tmp_path):
    rec = run_one("fem_cantilever", CommandAgent("sleep 5", timeout=1), LocalExecutor, 0, 1, str(tmp_path))
    assert rec["error"] == "timeout" and rec["failure_type"] == "agent_timeout"


def test_cli_agent_timeout_records_timeout_and_transcript(tmp_path):
    out = str(tmp_path / "results")
    started = time.monotonic()
    main([
        "--task", "fem_cantilever", "--agent", "cmd", "--cmd", "sleep 30",
        "--agent-name", "slow", "--executor", "local", "--allow-unsafe-local",
        "--agent-timeout", "5", "--out", out,
    ])
    elapsed = time.monotonic() - started

    result = json.loads((tmp_path / "results" / "fem_cantilever__slow__0.json").read_text())
    transcript = json.loads((tmp_path / "results" / "transcripts" / "fem_cantilever__slow__0.json").read_text())
    assert 4.5 <= elapsed < 10.0
    assert result["error"] == "timeout"
    assert result["failure_type"] == "agent_timeout"
    assert transcript[0]["timed_out"] is True


def test_agent_cannot_escape_workspace():
    with LocalExecutor("fem_cantilever") as ex:
        with pytest.raises(ValueError):
            ex.write_file("../../evil.py", "x")
        assert "reference" not in ex.bash("ls")
        assert not os.path.exists(os.path.join(ex.ws, "grader.py"))


def test_ci_95pct_on_binary_pass_rates():
    x = np.array([0.0, 1.0, 1.0, 1.0], dtype=float)
    lo, hi = ci(x)
    assert 0.0 <= lo <= 0.75 <= hi <= 1.0


def test_wilson_interval_handles_all_fail_and_all_pass_samples():
    fail_lo, fail_hi = ci([0, 0, 0, 0, 0])
    pass_lo, pass_hi = ci([1, 1, 1, 1, 1])
    assert fail_lo == 0.0 and fail_hi == pytest.approx(0.4345, abs=0.0001)
    assert pass_lo == pytest.approx(0.5655, abs=0.0001) and pass_hi == 1.0


# ---- failure taxonomy ----------------------------------------------------------------------------
def test_classify():
    assert classify(dict(passed=True), True, None) == "pass"
    assert classify(dict(passed=False, checks={"x": False}), False, None) == "no_attempt"
    assert classify(dict(passed=False, checks={"runs_without_error": False}), True, None) == "crash"
    assert classify(dict(passed=False, checks={"overshoot": False}), True, None) == "wrong_physics"
    assert classify(dict(passed=False, checks={"overshoot": False}), True, "max_steps_reached") == "ran_out_of_steps"
    assert classify(dict(passed=False, checks={"overshoot": False}), True, "timeout") == "agent_timeout"


# ---- CLI + analysis ------------------------------------------------------------------------------
def test_cli_and_report(tmp_path):
    out = str(tmp_path / "res")
    main(["--task", "fem_cantilever", "--agent", "oracle", "--executor", "local", "--out", out])
    main(["--task", "fem_cantilever", "--agent", "null", "--executor", "local", "--out", out])
    df = load(out)
    s = summarize(df, price_in=1, price_out=2).set_index("agent")
    assert s.loc["oracle", "pass_rate"] == 1.0 and s.loc["null", "pass_rate"] == 0.0 and "cost_usd" in s
    assert failure_table(df).loc[("fem_cantilever", "null"), "no_attempt"] == 1
    assert check_table(df).shape[0] == 2
    from analysis.report import main as rep
    rep(["--results", out, "--out", str(tmp_path / "rep")])
    assert (tmp_path / "rep" / "report.md").exists() and (tmp_path / "rep" / "pass_rate.png").exists()


def test_command_agent_refuses_local_executor():
    with pytest.raises(SystemExit):
        main(["--task", "fem_cantilever", "--agent", "cmd", "--cmd", "true", "--executor", "local"])


def test_missing_dependency_is_environment_error_not_agent_failure(monkeypatch):
    import json
    import harness.executors as E
    monkeypatch.setattr(E, "load_manifest", lambda n: {**json.load(open(f"tasks/{n}/task.json")), "requires": ["no_such_pkg_xyz"]})
    with pytest.raises(SystemExit, match="ENVIRONMENT ERROR"):
        main(["--task", "fem_cantilever", "--agent", "oracle", "--executor", "local", "--out", "/tmp/eb_env"])
