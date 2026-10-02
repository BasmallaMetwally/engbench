# EngBench

<p align="center">
  <a href="https://github.com/BasmallaMetwally/engbench/actions/workflows/ci.yml">
    <img src="https://github.com/BasmallaMetwally/engbench/actions/workflows/ci.yml/badge.svg" alt="CI" />
  </a>
  <img src="https://img.shields.io/badge/python-3.11%2B-blue" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/pytest-enabled-46C1FF" alt="Pytest" />
  <img src="https://img.shields.io/badge/status-active-success" alt="Status" />
</p>

EngBench is a benchmark for evaluating coding agents on engineering-intensive tasks that require scientific reasoning, simulation, and code generation under hidden deterministic constraints.

Each task includes:

- a realistic engineering problem
- a starter implementation
- an executable simulator or model
- a hidden reference solution
- a physics-based grader that evaluates correctness without exposing the oracle

The goal is to measure whether an agent can reason, write code, and produce valid engineering solutions rather than merely match a pattern.

## Why this project exists

Many benchmarks focus on generic coding or symbolic reasoning. EngBench instead targets engineering tasks where correctness depends on:

- numerical simulation
- physics-informed evaluation
- hidden parameterization
- convergence and stability checks
- adversarial validation against plausible but wrong solutions

This makes it well suited for benchmarking AI coding agents in scientific and simulation-heavy workflows.

## Benchmark tasks

| Task | Domain | Status |
| --- | --- | --- |
| `fem_cantilever` | Finite element method, plane stress, mesh convergence | Done |
| `control_pid_tuning` | Control systems, delayed plant, optimization, robustness | Done |
| `linear_model_fit` | Regression and model fitting under hidden conditions | Added |
| `cfd_channel_flow` | CFD / flow simulation | Planned |
| `circuit_rc_filter` | Circuit analysis and time-domain filtering | Planned |
| `embedded_blink_qemu` | Embedded firmware and QEMU validation | Planned |

## Design principles

- Graders measure physics, not code style.
- Hidden seeded instances prevent memorization.
- Every task is validated adversarially against bad-but-plausible solutions.
- Agents are isolated from the grader and oracle when used in Docker mode.
- Failures are classified as `no_attempt`, `crash`, `wrong_physics`, `ran_out_of_steps`, or `timeout`.

## Repository structure

```text
engbench/
├── README.md
├── requirements.txt
├── analysis/
│   └── report.py
├── harness/
│   ├── agents.py
│   ├── executors.py
│   └── run.py
├── tasks/
│   ├── fem_cantilever/
│   ├── control_pid_tuning/
│   └── ...
├── tests/
│   ├── test_mutants.py
│   ├── test_harness.py
│   └── ...
├── results/
└── .github/workflows/ci.yml
```

## Quick start

```bash
python -m pip install -r requirements.txt
pytest -q tests

# Baselines
python -m harness.run --task all --agent oracle --executor local
python -m harness.run --task all --agent null --executor local

# Generate a report from result JSON files
python -m analysis.report --results results --out report
```

> Real pass rates and confidence intervals should be computed from actual result JSON files stored under `results/`.

## Running tasks with a custom agent

```bash
python -m harness.run \
  --task all \
  --agent cmd \
  --cmd "<your agent command>" \
  --agent-name my_agent \
  --executor local \
  --allow-unsafe-local \
  --trials 5
```

## Validation model

The project includes automated validation for:

- reference solution passes
- starter code fails when it should
- adversarial wrong solutions are rejected
- mutation-style grader failures are caught
- harness behavior and CLI output remain stable

## Contribution

We welcome contributions that improve:

- new benchmark tasks
- grader robustness
- mutation and adversarial validation strategies
- analysis/reporting quality
- harness reliability and reproducibility

## Roadmap

See [ROADMAP.md](ROADMAP.md) for the next phase of work, including mutation generation automation, stricter CI thresholds, richer reporting, and new domain tasks.

## Suggested GitHub topics

Use these topics on the repository page:

- `benchmark`
- `ai-agents`
- `engineering`
- `simulation`
- `python`
- `scientific-computing`
- `control-systems`
- `finite-elements`
- `pytest`
- `docker`

