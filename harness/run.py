"""CLI: run agent(s) on task(s), grade, and write one JSON record per run.

  python -m harness.run --task all --agent oracle --executor local
"""
import argparse, datetime, json, os, time
from .agents import CommandAgent, NullAgent, OracleAgent
from .executors import DockerExecutor, LocalExecutor, TASKS_DIR


def classify(grade: dict, changed: bool, agent_error) -> str:
    """Failure taxonomy used by the analysis."""
    if grade.get("passed"):
        return "pass"
    if agent_error == "timeout":
        return "agent_timeout"
    if not changed:
        return "no_attempt"                       # solution.py identical to starter
    checks = grade.get("checks", {})
    if "grader_timeout" in checks:
        return "timeout"
    if "runs_without_error" in checks:
        return "crash"                            # raised / import error / NotImplemented
    if agent_error == "max_steps_reached":
        return "ran_out_of_steps"
    return "wrong_physics"                        # ran fine but failed physical checks


def run_one(task, agent, executor_cls, trial, max_steps, out_dir):
    with executor_cls(task) as ex:
        starter = ex.starter_solution()
        t0 = time.time()
        res = agent.run(ex, ex.task_prompt(), max_steps)
        agent_s = time.time() - t0
        try:
            changed = ex.read_file("solution.py") != starter
        except Exception:
            changed = False
        t1 = time.time()
        grade = ex.grade()
        grade_s = time.time() - t1
    rec = dict(task=task, agent=agent.name, model=agent.model, trial=trial,
               timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
               passed=bool(grade.get("passed")), score=float(grade.get("score", 0.0)),
               checks=grade.get("checks", {}), detail=grade.get("detail", {}),
               failure_type=classify(grade, changed, res["error"]), solution_changed=changed,
               steps=res["steps"], input_tokens=res["input_tokens"], output_tokens=res["output_tokens"],
               agent_seconds=round(agent_s, 2), grade_seconds=round(grade_s, 2), error=res["error"])
    os.makedirs(os.path.join(out_dir, "transcripts"), exist_ok=True)
    stem = f"{task}__{agent.name.replace(':', '_')}__{trial}"
    json.dump(rec, open(os.path.join(out_dir, stem + ".json"), "w"), indent=2)
    if res["transcript"]:
        json.dump(res["transcript"], open(os.path.join(out_dir, "transcripts", stem + ".json"), "w"), indent=1)
    return rec


def all_tasks():
    return sorted(d for d in os.listdir(TASKS_DIR) if os.path.exists(os.path.join(TASKS_DIR, d, "task.json")))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", default="all")
    ap.add_argument("--agent", choices=["null", "oracle", "cmd"], required=True)
    ap.add_argument("--cmd", help="shell command that runs your agent (for --agent cmd)")
    ap.add_argument("--agent-name", default="cmd")
    ap.add_argument("--executor", choices=["local", "docker"], default="docker")
    ap.add_argument("--trials", type=int, default=1)
    ap.add_argument("--max-steps", type=int, default=30)
    ap.add_argument("--out", default="results")
    ap.add_argument("--allow-unsafe-local", action="store_true",
                    help="permit an LLM agent to run bash directly on this machine (NOT recommended)")
    a = ap.parse_args(argv)

    if a.agent == "cmd" and not a.cmd:
        ap.error("--agent cmd needs --cmd")
    if a.agent == "cmd" and a.executor == "local" and not a.allow_unsafe_local:
        ap.error("Command agents must run in --executor docker (local has no isolation). Override: --allow-unsafe-local")
    agent = {"null": NullAgent, "oracle": OracleAgent}.get(a.agent, lambda: CommandAgent(a.cmd, a.agent_name))()
    ex_cls = LocalExecutor if a.executor == "local" else DockerExecutor
    tasks = all_tasks() if a.task == "all" else [a.task]
    for task in tasks:
        for trial in range(a.trials):
            try:
                r = run_one(task, agent, ex_cls, trial, a.max_steps, a.out)
            except EnvironmentError as e:
                raise SystemExit(f"ENVIRONMENT ERROR (not an agent failure): {e}")
            print(f"{task:22s} {agent.name:28s} trial {trial}: {r['failure_type']:14s} score={r['score']:.2f} "
                  f"steps={r['steps']} tokens={r['input_tokens']}+{r['output_tokens']}")


if __name__ == "__main__":
    main()
