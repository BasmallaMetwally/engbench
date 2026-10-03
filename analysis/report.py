"""Aggregate results/*.json -> report.md + PNG charts.

  python -m analysis.report --results results --out report
  python -m analysis.report --results results --out report --price-in 3 --price-out 15   # $/M tokens (you supply)
"""
import argparse, glob, json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def ci(x):
    """Return the two-sided 95% Wilson score interval for binary outcomes."""
    x = np.asarray(x, dtype=float)
    if x.size == 0:
        return np.array([np.nan, np.nan])
    if not np.isin(x, [0.0, 1.0]).all():
        raise ValueError("Wilson intervals require binary observations (0 or 1)")
    n = x.size
    successes = float(x.sum())
    z = 1.959963984540054
    z2 = z * z
    proportion = successes / n
    denominator = 1.0 + z2 / n
    center = (proportion + z2 / (2.0 * n)) / denominator
    half_width = z * np.sqrt(proportion * (1.0 - proportion) / n + z2 / (4.0 * n * n)) / denominator
    return np.array([max(0.0, center - half_width), min(1.0, center + half_width)])


def load(results_dir: str) -> pd.DataFrame:
    rows = [json.load(open(p)) for p in glob.glob(os.path.join(results_dir, "*.json"))]
    if not rows:
        raise SystemExit(f"no result files in {results_dir}")
    return pd.DataFrame(rows)


def summarize(df: pd.DataFrame, price_in=None, price_out=None) -> pd.DataFrame:
    g = df.groupby(["task", "agent"])
    s = g.agg(runs=("passed", "size"), pass_rate=("passed", "mean"), mean_score=("score", "mean"),
              mean_steps=("steps", "mean"), in_tok=("input_tokens", "mean"), out_tok=("output_tokens", "mean"),
              agent_s=("agent_seconds", "mean")).reset_index()
    ci_rows = []
    for (task, agent), group in g:
        lo, hi = ci(group["passed"].to_numpy(dtype=float))
        ci_rows.append({"task": task, "agent": agent,
                "pass_rate_wilson_ci_low": float(lo), "pass_rate_wilson_ci_high": float(hi)})
    if ci_rows:
        s = s.merge(pd.DataFrame(ci_rows), on=["task", "agent"], how="left")
    if price_in is not None and price_out is not None:
        s["cost_usd"] = np.where((s.in_tok + s.out_tok) > 0,
                                (s.in_tok * price_in + s.out_tok * price_out) / 1e6,
                                np.nan)
    return s


def mutation_score(rows) -> pd.DataFrame:
    """Rows must include task, mutant, and either killed or passed."""
    if rows is None:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    if df.empty or not {"task", "mutant"}.issubset(df.columns):
        return pd.DataFrame()
    if "killed" not in df.columns:
        if "passed" not in df.columns:
            return pd.DataFrame()
        df["killed"] = (~df["passed"].astype(bool)).astype(int)
    return (df.groupby("task", as_index=False)
            .agg(mutants=("mutant", "count"), killed=("killed", "sum"))
            .assign(mutation_score=lambda d: d["killed"] / d["mutants"]))


def failure_table(df):
    return pd.crosstab([df.task, df.agent], df.failure_type)


def check_table(df):
    """Per-check pass rate (which physical requirement do agents miss most?)."""
    recs = [dict(task=r.task, agent=r.agent, check=k, ok=bool(v)) for r in df.itertuples() for k, v in r.checks.items()]
    return pd.DataFrame(recs).groupby(["task", "agent", "check"]).ok.mean().unstack("check").round(2)


def per_task_checks(df) -> str:
    ct, out = check_table(df), []
    for task in ct.index.get_level_values("task").unique():
        sub = ct.xs(task, level="task").dropna(axis=1, how="all")
        out.append(f"### {task}\n\n" + md(sub))
    return "\n\n".join(out)


def md(df: pd.DataFrame) -> str:
    return df.round(3).to_markdown() if hasattr(df, "to_markdown") else df.to_string()


def plots(df, summ, out):
    fig, ax = plt.subplots(figsize=(7, 4))
    summ.pivot(index="task", columns="agent", values="pass_rate").plot.bar(ax=ax, rot=15)
    ax.set_ylabel("pass rate"); ax.set_ylim(0, 1.05); ax.set_title("Pass rate by task and agent")
    fig.tight_layout(); fig.savefig(os.path.join(out, "pass_rate.png"), dpi=150); plt.close(fig)

    ft = pd.crosstab(df.agent, df.failure_type)
    fig, ax = plt.subplots(figsize=(7, 4))
    ft.plot.bar(stacked=True, ax=ax, rot=15); ax.set_ylabel("runs"); ax.set_title("Outcome / failure types")
    fig.tight_layout(); fig.savefig(os.path.join(out, "failure_types.png"), dpi=150); plt.close(fig)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results"); ap.add_argument("--out", default="report")
    ap.add_argument("--price-in", type=float); ap.add_argument("--price-out", type=float)
    ap.add_argument("--mutation", help="optional JSON file with mutation rows: [{'task': ..., 'mutant': ..., 'killed': ...}]")
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    df = load(a.results); summ = summarize(df, a.price_in, a.price_out)
    mut = pd.DataFrame()
    if a.mutation:
        with open(a.mutation) as fh:
            payload = json.load(fh)
        mut = mutation_score(payload)
    plots(df, summ, a.out)
    report = "# EngBench report\n\n## Summary\n\n" + md(summ.set_index(["task", "agent"]))
    if not mut.empty:
        report += "\n\n## Mutation score\n\n" + md(mut)
    report += (
        "\n\n## Failure types (runs)\n\n" + md(failure_table(df)) +
        "\n\n## Per-check pass rate\n\n" + per_task_checks(df) +
        "\n\n![pass rate](pass_rate.png)\n\n![failures](failure_types.png)\n"
    )
    with open(os.path.join(a.out, "report.md"), "w") as f:
        f.write(report)
    print(open(os.path.join(a.out, "report.md")).read())


if __name__ == "__main__":
    main()
