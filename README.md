# EngBench

A benchmark of simulation-based engineering tasks for evaluating AI coding / terminal agents.
Each task = Docker image + starter code + **deterministic physics-based grader** + hidden reference solution.

| Task | Skills | Status |
|---|---|---|
| `fem_cantilever` | FEM (scikit-fem), plane stress, mesh convergence | done |
| `control_pid_tuning` | control systems, delayed plant, SciPy optimisation, robustness | done |
| `cfd_channel_flow` | CFD (OpenFOAM) | planned |
| `circuit_rc_filter` | ngspice / LTspice-compatible | planned |
| `embedded_blink_qemu` | embedded firmware on QEMU | planned |

## Design principles
- **Graders measure physics, not code style**, and run on *hidden* seeded instances, so answers can't be memorised.
- **Every task is validated adversarially** (`tests/`): the reference passes; the untouched starter, hard-coded answers,
  closed-form shortcuts and plausible-but-wrong solutions must fail.
- **The agent never sees the grader or reference**: in Docker mode they are mounted read-only into a *separate*
  grading container with no network.
- Failures are classified: `no_attempt`, `crash`, `wrong_physics`, `ran_out_of_steps`, `timeout`.

## Quick start
    python -m pip install -r requirements.txt     # use the SAME interpreter you run the harness with
    pytest -q tests                                              # validate all tasks + harness

    # baselines (no API key): oracle = ceiling (must be 100%), null = floor (must be 0%)
    python -m harness.run --task all --agent oracle --executor local
    python -m harness.run --task all --agent null   --executor local

    # evaluate a custom command agent inside the workspace
    python -m harness.run --task all --agent cmd --cmd "<your agent command>" --agent-name my_agent --executor local --allow-unsafe-local --trials 5

    python -m analysis.report --results results --out report     # report.md + charts
    # add --price-in / --price-out ($ per million tokens) to get cost columns

> Real pass rates and confidence intervals must come from actual result JSON files under `results/`.
> The only hard numbers currently established in the repo are the baselines: `oracle` = 100% and `null` = 0%.

> `--executor local` has **no isolation**; the harness refuses to run a command agent with it unless you pass
> `--allow-unsafe-local`. Use Docker for real evaluations when you want a no-network sandbox.
> If your command agent talks to an external API, run it outside the no-network container or allow network only for the agent while keeping the grader container isolated.
> `--max-steps` is relevant for looped agents, but command agents are effectively single-shot shells and ignore a step budget.

## Layout
    tasks/<name>/{README.md, task.json, Dockerfile, starter/, reference/, grader.py}
    harness/   executors (local/docker), agents (null/oracle/cmd), CLI
    analysis/  pandas + matplotlib report
    tests/     task validation + harness tests (command-agent checks)
