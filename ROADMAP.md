# Roadmap

This roadmap describes the next engineering milestones for the project.

## Phase 1 — Stronger grader validation

### Issue 1: Automate mutation generation for task graders
- Generate variants of each task solution that intentionally break physics, numerics, or assumptions.
- Measure the mutant rejection rate; the existing hand-authored suite currently enforces a 90% mutation score.
- Extend mutation testing to generated variants and publish the score in the report.

### Issue 2: Enforce strict CI gating and report the score
- Fail CI if the configured mutation-score threshold is missed.
- Block merges when grader validation or harness tests regress.
- Include a summary table in the report with mutation counts and score.

### Issue 3: Improve report generation
- Add explicit pass-rate summaries by task and agent.
- Surface confidence intervals and failure taxonomy in generated reports.
- Keep the report sourced from result JSON files rather than static values.

## Phase 2 — Broader benchmark coverage

### Issue 4: Add more engineering tasks
- `cfd_channel_flow`
- `circuit_rc_filter`
- `embedded_blink_qemu`
- Add realistic hidden evaluations and deterministic graders for each task.

### Issue 5: Create a standard task template
- Define a reusable scaffold with `README`, `task.json`, `Dockerfile`, `starter`, `reference`, and `grader`.
- Reduce authoring friction for new benchmark additions.

## Phase 3 — Reproducibility and operational quality

### Issue 6: Make benchmarking reproducible
- Version-lock task data and run seeds.
- Document deterministic local and Docker execution.

### Issue 7: Improve security and sandboxing
- Document the no-network grading setup.
- Add safer defaults for local and remote task execution.

### Issue 8: Improve contribution quality
- Add contribution guidance and issue templates.
- Standardize naming and validation checks for task authors.

## Suggested issue backlog for GitHub

1. Automate mutant generation for grader validation
2. Enforce CI threshold and mutation-score reporting
3. Add task-level summaries and confidence intervals to reports
4. Add a CFD benchmark task
5. Add a circuit-analysis benchmark task
6. Add an embedded-firmware benchmark task
7. Standardize the task-authoring template
8. Improve sandboxing and no-network documentation
