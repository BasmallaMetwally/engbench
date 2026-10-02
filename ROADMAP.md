# Roadmap

This roadmap describes the next engineering milestones for the project.

## Phase 1 — Stronger grader validation

### Issue 1: Automate mutation generation for task graders
+- Generate automated variants of each task solution that intentionally break physics, numerics, or assumptions.
+- Ensure the grader rejects the broken variants with a high pass rate.
+- Target: mutation score >= 90% for integrated grader tests.
+
### Issue 2: Enforce strict CI gating
+- Fail CI if mutation score is below the configured threshold.
+- Block merges when grader validation or harness tests regress.
+- Add a summary table in the report that prints the mutation score.
+
### Issue 3: Improve report generation
+- Add explicit pass-rate summaries by task and agent.
+- Surface confidence intervals and failure taxonomy in generated reports.
+- Keep the report sourced from result JSON files rather than static values.
+
## Phase 2 — Broader benchmark coverage
+
### Issue 4: Add more engineering tasks
+- `cfd_channel_flow`
+- `circuit_rc_filter`
+- `embedded_blink_qemu`
+- Additional tasks with realistic hidden evaluations and deterministic grading.
+
### Issue 5: Create a standard task template
+- Define a reusable scaffold for tasks with `README`, `task.json`, `Dockerfile`, `starter`, `reference`, and `grader` layout.
+- Reduce authoring friction for new benchmark additions.
+
## Phase 3 — Reproducibility and operational quality
+
### Issue 6: Make benchmarking reproducible
+- Version lock task data and run seeds.
+- Provide a documented recipe for deterministic local and Docker execution.
+
### Issue 7: Improve security and sandboxing
+- Document the no-network grading setup.
+- Add safer defaults for local and remote task execution.
+
### Issue 8: Improve contribution quality
+- Add contribution guide and issue templates.
+- Standardize naming and validation checks for task authors.
+
## Suggested issue backlog for GitHub
+
+1. Automate mutant generation for grader validation
+2. Enforce CI threshold and mutation score reporting
+3. Add task-level summary and confidence intervals to report output
+4. Add new CFD benchmark task
+5. Add circuit-analysis benchmark task
+6. Add embedded firmware benchmark task
+7. Standardize task authoring template
+8. Improve sandboxing and no-network execution docs
